"""Runs ElastiCache nodes as Docker containers (issue #3, phase 2).

Moto stores the ElastiCache resources. This module adds the servers:

- A replication group (cluster mode disabled) gets one container per member
  cluster: the first is the primary, the others replicate from it
  (``--replicaof``). The group and its member clusters are ``creating`` until
  every node answers, then ``available``.
- A cache cluster created on its own (CreateCacheCluster without a
  replication group) gets one container.
- ``valkey`` and ``redis`` use ``valkey/valkey:<major>`` and ``redis:<major>``;
  ``memcached`` uses ``memcached:<major>.<minor>``.
- ``AuthToken`` sets the server password (``--requirepass``; replicas also get
  ``--masterauth``).
- The primary of a replication group listens on the group's port (``Port``,
  default 6379) on mocksy's host, so OpenTofu/Terraform see no change. The
  ``PrimaryEndpoint`` and ``ReaderEndpoint`` both use it. Each node is also
  reachable on its own port of mocksy's external range through its member
  ``ReadEndpoint`` (see ``container_resources``).
- With ``TransitEncryptionEnabled``, the port accepts TLS with mocksy's
  certificate for ``localhost.localstack.cloud`` and forwards plain TCP to the
  server, so any image works.
- DeleteReplicationGroup and DeleteCacheCluster remove the containers.

Cluster mode (sharding), and all engines when Docker is not available or
``ELASTICACHE_RUN_CONTAINERS=0``, are recorded only, as in phase 1.
"""

from __future__ import annotations

import logging
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from localstack import config
from localstack.services.container_resources import (
    LABEL_RESOURCE,
    ContainerResource,
    ContainerResourceError,
    container_name,
    docker_available,
)

LOG = logging.getLogger(__name__)

REDIS_PORT = 6379
MEMCACHED_PORT = 11211
REDIS_LIKE = ("redis", "valkey")


def _image(engine: str, version: str) -> str:
    parts = (version or "").split(".")
    major = parts[0] if parts and parts[0] else ""
    minor = f"{major}.{parts[1]}" if len(parts) > 1 else major
    template = {
        "valkey": config.ELASTICACHE_VALKEY_IMAGE,
        "redis": config.ELASTICACHE_REDIS_IMAGE,
        "memcached": config.ELASTICACHE_MEMCACHED_IMAGE,
    }[engine]
    return template.format(major=major, minor=minor)


def _server_command(engine: str, token: str | None, primary_ip: str | None) -> list[str]:
    if engine == "memcached":
        return ["memcached", "-p", str(MEMCACHED_PORT)]
    server = "valkey-server" if engine == "valkey" else "redis-server"
    command = [server, "--port", str(REDIS_PORT), "--protected-mode", "no", "--appendonly", "no"]
    if token:
        command += ["--requirepass", token]
    if primary_ip:
        command += ["--replicaof", primary_ip, str(REDIS_PORT)]
        if token:
            command += ["--masterauth", token]
    return command


def _cli(engine: str) -> str:
    return "valkey-cli" if engine == "valkey" else "redis-cli"


class CacheRunner:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        # cache cluster ID (per account and region) -> container
        self._nodes: dict[tuple[str, str, str], ContainerResource] = {}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="elasticache")
        self._docker: bool | None = None

    def _enabled(self) -> bool:
        if not config.ELASTICACHE_RUN_CONTAINERS:
            return False
        if self._docker is None:
            self._docker = docker_available()
            if not self._docker:
                LOG.warning("Docker is not available: ElastiCache clusters are recorded only")
        return self._docker

    # --------------------------------------------------------- replication groups

    def create_group(self, backend: Any, group: Any, token: str | None) -> None:
        engine = (group.engine or "redis").lower()
        if not self._enabled() or engine not in REDIS_LIKE or group.cluster_enabled:
            return
        group.status = "creating"
        for cluster_id in group.member_clusters:
            cluster = backend.cache_clusters.get(cluster_id)
            if cluster is not None:
                cluster.cache_cluster_status = "creating"
        self._executor.submit(self._start_group, backend, group, engine, token)

    def _start_group(self, backend: Any, group: Any, engine: str, token: str | None) -> None:
        members = list(group.member_clusters)
        started: dict[str, ContainerResource] = {}
        try:
            primary_ip = None
            for index, cluster_id in enumerate(members):
                if self._deleted(group):
                    return
                cluster = backend.cache_clusters.get(cluster_id)
                version = getattr(cluster, "engine_version", None) or group.engine_version or ""
                node = self._start_node(
                    backend,
                    cluster_id,
                    engine,
                    version,
                    token,
                    primary_ip=primary_ip if index > 0 else None,
                    tls=bool(group.transit_encryption_enabled),
                    arn=group.arn,
                    started=started,
                    # the primary listens on the group's port, see _publish_group_endpoints
                    fixed_port=self._group_port(group) if index == 0 else None,
                )
                if index == 0:
                    primary_ip = node.network_ip
            for cluster_id, node in started.items():
                self._wait_ready(node, engine, token, replica=cluster_id != members[0], owner=group)
            if self._deleted(group):
                return
            self._publish_group_endpoints(backend, group, started)
            for cluster_id in members:
                cluster = backend.cache_clusters.get(cluster_id)
                if cluster is not None:
                    cluster.cache_cluster_status = "available"
            group.status = "available"
        except Exception as e:
            if not self._deleted(group):
                LOG.warning("Replication group %s cannot start: %s", group.replication_group_id, e)
                group.status = "create-failed"
                self.delete_group(backend, group)
        finally:
            # a delete during creation finds no container yet; remove what was started here
            if self._deleted(group):
                for node in started.values():
                    node.stop(remove=True)

    @staticmethod
    def _deleted(resource: Any) -> bool:
        return resource.__dict__.get("_mocksy_deleted", False)

    @staticmethod
    def _group_port(group: Any) -> int:
        return int(getattr(group, "_mocksy_requested_port", None) or REDIS_PORT)

    def _publish_group_endpoints(
        self, backend: Any, group: Any, nodes: dict[str, ContainerResource]
    ) -> None:
        """Set the endpoints that DescribeReplicationGroups returns.

        The primary and reader endpoints use the group's port (the ``Port`` of the
        request, default 6379). OpenTofu/Terraform treat the group's port as an input,
        so another port would replace the group on every plan. Both endpoints reach the
        primary, because one address and port can reach only one node. Each member's
        ``ReadEndpoint`` reaches that node on its own port.
        """
        members = list(group.member_clusters)
        primary = nodes[members[0]]
        for node_group in group.node_groups:
            node_group["primary_endpoint_address"] = primary.endpoint_host
            node_group["reader_endpoint_address"] = primary.endpoint_host
            node_group["port"] = primary.external_port
            node_group["primary_endpoint"] = {
                "address": primary.endpoint_host,
                "port": primary.external_port,
            }
            # Moto has no ReaderEndpoint; AWS returns it and OpenTofu/Terraform read it
            node_group["reader_endpoint"] = {
                "address": primary.endpoint_host,
                "port": primary.external_port,
            }
            for member in node_group.get("node_group_members", []):
                node = nodes.get(member.get("cache_cluster_id"))
                if node is not None:
                    member["read_endpoint"] = {
                        "address": node.endpoint_host,
                        "port": node.external_port,
                    }
        group.port = primary.external_port
        for cluster_id, node in nodes.items():
            self._publish_cluster_endpoint(backend.cache_clusters.get(cluster_id), node)

    def delete_group(self, backend: Any, group: Any, members: list[str] | None = None) -> None:
        """Remove the nodes of a group. ``members`` are the member IDs before Moto changed them."""
        group._mocksy_deleted = True
        for cluster_id in members if members is not None else list(group.member_clusters):
            self._remove_node(backend, cluster_id)

    # ------------------------------------------------------- standalone clusters

    def create_cluster(self, backend: Any, cluster: Any, token: str | None) -> None:
        """Start a cache cluster that does not belong to a replication group."""
        engine = (cluster.engine or "redis").lower()
        if not self._enabled() or engine not in (*REDIS_LIKE, "memcached"):
            return
        cluster.cache_cluster_status = "creating"
        self._executor.submit(self._start_cluster, backend, cluster, engine, token)

    def _start_cluster(self, backend: Any, cluster: Any, engine: str, token: str | None) -> None:
        started: dict[str, ContainerResource] = {}
        try:
            node = self._start_node(
                backend,
                cluster.cache_cluster_id,
                engine,
                cluster.engine_version or "",
                token,
                primary_ip=None,
                tls=bool(getattr(cluster, "transit_encryption_enabled", False)),
                arn=cluster.arn,
                started=started,
            )
            self._wait_ready(node, engine, token, replica=False, owner=cluster)
            if self._deleted(cluster):
                return
            self._publish_cluster_endpoint(cluster, node)
            cluster.cache_cluster_status = "available"
        except Exception as e:
            if not self._deleted(cluster):
                LOG.warning("Cache cluster %s cannot start: %s", cluster.cache_cluster_id, e)
                cluster.cache_cluster_status = "create-failed"
                self._remove_node(backend, cluster.cache_cluster_id)
        finally:
            if self._deleted(cluster):
                for node in started.values():
                    node.stop(remove=True)

    def delete_cluster(self, backend: Any, cluster: Any) -> None:
        cluster._mocksy_deleted = True
        self._remove_node(backend, cluster.cache_cluster_id)

    @staticmethod
    def _publish_cluster_endpoint(cluster: Any, node: ContainerResource) -> None:
        if cluster is None:
            return
        cluster.port = node.external_port
        cluster.cache_nodes = [
            {
                "cache_node_id": "0001",
                "cache_node_status": "available",
                "endpoint": {"address": node.endpoint_host, "port": node.external_port},
            }
        ]
        if cluster.engine == "memcached":
            cluster.configuration_endpoint = {
                "address": node.endpoint_host,
                "port": node.external_port,
            }

    # --------------------------------------------------------------- nodes

    def _start_node(
        self,
        backend: Any,
        cluster_id: str,
        engine: str,
        version: str,
        token: str | None,
        primary_ip: str | None,
        tls: bool,
        arn: str,
        started: dict[str, ContainerResource],
        fixed_port: int | None = None,
    ) -> ContainerResource:
        key = (backend.account_id, backend.region_name, cluster_id)
        node = ContainerResource(
            name=container_name("elasticache", backend.account_id, backend.region_name, cluster_id),
            image=_image(engine, version),
            internal_port=MEMCACHED_PORT if engine == "memcached" else REDIS_PORT,
            tls=tls,
        )
        with self._lock:
            self._nodes[key] = node
        started[cluster_id] = node
        node.start(
            command=_server_command(engine, token, primary_ip),
            labels={LABEL_RESOURCE: arn},
            fixed_port=fixed_port,
        )
        return node

    def _wait_ready(
        self, node: ContainerResource, engine: str, token: str | None, replica: bool, owner: Any
    ) -> None:
        if engine == "memcached":

            def _memcached_ready() -> bool:
                if self._deleted(owner):
                    raise ContainerResourceError("deleted while it was created")
                with socket.create_connection((node.target_host, node.target_port), timeout=2) as s:
                    s.sendall(b"version\r\n")
                    return s.recv(64).startswith(b"VERSION")

            node.wait_until(
                _memcached_ready, timeout=config.ELASTICACHE_START_TIMEOUT, what="memcached ready"
            )
            return
        cli = [_cli(engine), "-p", str(REDIS_PORT), "--no-auth-warning"]
        if token:
            cli += ["-a", token]

        def _ready() -> bool:
            if self._deleted(owner):
                raise ContainerResourceError("deleted while it was created")
            if "PONG" not in node.exec([*cli, "PING"]):
                return False
            if replica:
                return "master_link_status:up" in node.exec([*cli, "INFO", "replication"])
            return True

        node.wait_until(_ready, timeout=config.ELASTICACHE_START_TIMEOUT, what="server ready")

    def _remove_node(self, backend: Any, cluster_id: str) -> None:
        with self._lock:
            node = self._nodes.pop((backend.account_id, backend.region_name, cluster_id), None)
        if node is not None:
            node.stop(remove=True)

    def shutdown(self) -> None:
        with self._lock:
            nodes = list(self._nodes.values())
            self._nodes.clear()
        for node in nodes:
            node.stop(remove=True)


CACHE_RUNNER = CacheRunner()
