"""Server containers behind a mocksy port (used by RDS and ElastiCache).

A resource such as an RDS instance runs as a Docker container. mocksy reserves a
port from its external service port range (``EXTERNAL_SERVICE_PORTS_START`` to
``EXTERNAL_SERVICE_PORTS_END``, default 4510-4559) and forwards it to the
server in the container. The endpoint is ``<LOCALSTACK_HOST host>:<port>``, so
clients on the host and in other containers use the same address, as with
mocksy's OpenSearch.

- When mocksy runs in Docker, the server container joins mocksy's network and
  the proxy connects to the container's IP.
- When mocksy runs on the host, the container port is published on 127.0.0.1
  and the proxy connects to that port. This also works on macOS and Windows,
  where container IPs cannot be reached from the host.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from localstack import config
from localstack.utils.container_networking import get_main_container_network
from localstack.utils.container_utils.container_client import PortMappings
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.net import PortNotAvailableException, get_free_tcp_port
from localstack.utils.server.tcp_proxy import TCPProxy
from localstack.utils.urls import localstack_host

LOG = logging.getLogger(__name__)

LABEL_MANAGED = "mocksy.resource.managed"
LABEL_RESOURCE = "mocksy.resource.arn"

# reserved ports stay reserved as long as the resource exists
_PORT_RESERVATION_SECONDS = 10 * 365 * 24 * 3600


class ContainerResourceError(Exception):
    """The container of a resource cannot start or does not become ready."""


def docker_available() -> bool:
    try:
        return DOCKER_CLIENT.has_docker()
    except Exception:
        return False


def container_name(prefix: str, *parts: str) -> str:
    raw = "-".join(["mocksy", prefix, *parts])
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", raw)[:128]


@dataclass
class ContainerResource:
    """A running server container and the proxy that exposes it."""

    name: str
    image: str
    internal_port: int
    container_id: str = ""
    network: str | None = None
    # address that the proxy, and other server containers, use to reach the server
    target_host: str = ""
    target_port: int = 0
    # address of the server on the Docker network (for replication between containers)
    network_ip: str = ""
    external_port: int = 0
    proxy: TCPProxy | None = field(default=None, repr=False)

    @property
    def endpoint_host(self) -> str:
        return localstack_host().host

    # ------------------------------------------------------------ lifecycle

    def start(
        self,
        env: dict[str, str] | None = None,
        command: list[str] | str | None = None,
        entrypoint: list[str] | str | None = None,
        labels: dict[str, str] | None = None,
        preferred_port: int | None = None,
    ) -> None:
        """Pull the image if needed, start the container and the proxy."""
        self._pull_image()
        self.network = get_main_container_network()
        ports = None
        if not config.is_in_docker:
            host_port = get_free_tcp_port()
            ports = PortMappings(bind_host="127.0.0.1")
            ports.add(host_port, self.internal_port)
            self.target_host, self.target_port = "127.0.0.1", host_port

        DOCKER_CLIENT.remove_container(self.name, force=True, check_existence=True)
        self.container_id = DOCKER_CLIENT.create_container(
            self.image,
            name=self.name,
            env_vars=env,
            command=command,
            entrypoint=entrypoint,
            network=self.network,
            ports=ports,
            labels={LABEL_MANAGED: "true", **(labels or {})},
        )
        DOCKER_CLIENT.start_container(self.container_id)
        self.network_ip = DOCKER_CLIENT.get_container_ipv4_for_network(
            self.container_id, self.network
        )
        if config.is_in_docker:
            self.target_host, self.target_port = self.network_ip, self.internal_port
        self._start_proxy(preferred_port)

    def _pull_image(self) -> None:
        try:
            DOCKER_CLIENT.inspect_image(self.image, pull=False)
            return
        except Exception:
            pass
        try:
            DOCKER_CLIENT.pull_image(self.image)
        except Exception as e:
            raise ContainerResourceError(f"Cannot pull image {self.image}: {e}") from e

    def _start_proxy(self, preferred_port: int | None) -> None:
        from localstack.utils.common import external_service_ports

        port = None
        if preferred_port:
            try:
                port = external_service_ports.reserve_port(
                    preferred_port, duration=_PORT_RESERVATION_SECONDS
                )
            except PortNotAvailableException:
                LOG.info("Port %s is not available, using another port", preferred_port)
        if port is None:
            try:
                port = external_service_ports.reserve_port(duration=_PORT_RESERVATION_SECONDS)
            except PortNotAvailableException as e:
                raise ContainerResourceError(
                    "No free port in EXTERNAL_SERVICE_PORTS_START..EXTERNAL_SERVICE_PORTS_END"
                ) from e
        self.external_port = port
        self.proxy = TCPProxy(
            target_address=self.target_host,
            target_port=self.target_port,
            port=port,
            host=config.GATEWAY_LISTEN[0].host if config.GATEWAY_LISTEN else "0.0.0.0",
        )
        self.proxy.start()

    def stop(self, remove: bool = True) -> None:
        """Stop the proxy and the container. ``remove`` also deletes the container and its data."""
        if self.proxy:
            try:
                self.proxy.shutdown()
            except Exception as e:
                LOG.debug("Cannot stop proxy on port %s: %s", self.external_port, e)
            self.proxy = None
        self._release_port()
        if not self.container_id:
            return
        try:
            if remove:
                DOCKER_CLIENT.remove_container(self.container_id, force=True)
            else:
                DOCKER_CLIENT.stop_container(self.container_id, timeout=10)
        except Exception as e:
            LOG.debug("Cannot stop container %s: %s", self.name, e)

    def restart(self) -> None:
        """Restart the container; the endpoint stays the same."""
        DOCKER_CLIENT.restart_container(self.container_id)
        self._refresh_target()

    def resume(self) -> None:
        """Start a stopped container again and expose it on a new reserved port."""
        DOCKER_CLIENT.start_container(self.container_id)
        self._refresh_target()
        self._start_proxy(self.external_port or None)

    def _refresh_target(self) -> None:
        # the container IP or the published port can change after a restart
        self.network_ip = DOCKER_CLIENT.get_container_ipv4_for_network(
            self.container_id, self.network
        )
        if config.is_in_docker:
            self.target_host = self.network_ip
        else:
            published = DOCKER_CLIENT.inspect_container(self.container_id)["NetworkSettings"][
                "Ports"
            ].get(f"{self.internal_port}/tcp")
            if published:
                self.target_port = int(published[0]["HostPort"])
        if self.proxy:
            self.proxy._target_address = self.target_host
            self.proxy._target_port = self.target_port

    def _release_port(self) -> None:
        if not self.external_port:
            return
        from localstack.utils.common import external_service_ports

        try:
            external_service_ports._ports_cache.pop(self.external_port, None)
        except Exception:
            pass

    # -------------------------------------------------------------- helpers

    def exec(self, command: list[str], env: dict[str, str] | None = None) -> str:
        stdout, _ = DOCKER_CLIENT.exec_in_container(self.container_id, command, env_vars=env)
        return stdout.decode() if isinstance(stdout, bytes) else str(stdout)

    def is_running(self) -> bool:
        try:
            return bool(DOCKER_CLIENT.inspect_container(self.container_id)["State"]["Running"])
        except Exception:
            return False

    def logs(self) -> str:
        try:
            return DOCKER_CLIENT.get_container_logs(self.container_id, safe=True)
        except Exception:
            return ""

    def wait_until(self, check: Callable[[], bool], timeout: float, what: str) -> None:
        """Call ``check`` until it returns True. Fails early when the container stops."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if check():
                    return
            except ContainerResourceError:
                raise
            except Exception as e:
                LOG.debug("%s: %s not ready yet: %s", self.name, what, e)
            if not self.is_running():
                raise ContainerResourceError(
                    f"Container {self.name} stopped before {what}. Last output:\n"
                    + self.logs()[-2000:]
                )
            time.sleep(0.5)
        raise ContainerResourceError(
            f"Timeout: {what} ({timeout:.0f}s) for {self.name}. Last output:\n"
            + self.logs()[-2000:]
        )
