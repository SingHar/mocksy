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
import select
import socket
import ssl
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


class TLSTerminatingProxy(TCPProxy):
    """A TCP proxy that accepts TLS from clients and forwards plain TCP to the server.

    The certificate is mocksy's certificate for ``localhost.localstack.cloud``.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        from localstack.utils.ssl import create_ssl_cert

        _, cert_file, key_file = create_ssl_cert()
        self._ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self._ssl_context.load_cert_chain(cert_file, key_file)

    def _handle_request(self, s_src: socket.socket):
        try:
            s_src.settimeout(10)
            tls_src = self._ssl_context.wrap_socket(s_src, server_side=True)
            tls_src.settimeout(None)
        except Exception as e:
            LOG.debug("TLS handshake on port %s failed: %s", self.port, e)
            s_src.close()
            return
        try:
            with (
                tls_src,
                socket.create_connection(
                    (self._target_address, self._target_port), timeout=10
                ) as s_dst,
            ):
                s_dst.settimeout(None)
                while not self._stopped.is_set():
                    # decrypted bytes can wait inside the TLS object, where select() cannot see them
                    readable = [tls_src] if tls_src.pending() else []
                    if not readable:
                        readable, _, _ = select.select([tls_src, s_dst], [], [], 1)
                    for sock in readable:
                        data = sock.recv(65536)
                        if not data:
                            return
                        (s_dst if sock is tls_src else tls_src).sendall(data)
        except (OSError, ssl.SSLError) as e:
            LOG.debug("TLS proxy connection on port %s closed: %s", self.port, e)


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
    # accept TLS on the external port (the server in the container uses plain TCP)
    tls: bool = False
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
        fixed_port: int | None = None,
    ) -> None:
        """Pull the image if needed, start the container and the proxy.

        :param preferred_port: a port of the external range to try first
        :param fixed_port: a port outside the range to listen on (for example 6379), used
            when it is free; otherwise a range port is used. ``external_port`` shows the result.
        """
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
        self._start_proxy(preferred_port, fixed_port)

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

    @property
    def _listen_host(self) -> str:
        return config.GATEWAY_LISTEN[0].host if config.GATEWAY_LISTEN else "0.0.0.0"

    def _port_is_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self._listen_host, port))
                return True
            except OSError:
                return False

    def _start_proxy(self, preferred_port: int | None, fixed_port: int | None = None) -> None:
        from localstack.utils.common import external_service_ports

        port = None
        self.fixed_port_used = False
        if fixed_port:
            if self._port_is_free(fixed_port):
                port = fixed_port
                self.fixed_port_used = True
            else:
                LOG.warning(
                    "Port %s for %s is in use; using a port of the external range instead",
                    fixed_port,
                    self.name,
                )
        if port is None and preferred_port:
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
        proxy_class = TLSTerminatingProxy if self.tls else TCPProxy
        self.proxy = proxy_class(
            target_address=self.target_host,
            target_port=self.target_port,
            port=port,
            host=self._listen_host,
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
        if not self.external_port or getattr(self, "fixed_port_used", False):
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
