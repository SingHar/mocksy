"""ElastiCache provider.

Phase 1: operations are handled by Moto through the MotoFallbackDispatcher.
Clusters are recorded but no Valkey or Redis server runs yet (see issue #3, phase 2).

Fixes on top of Moto:
- In AWS, creating a replication group also creates one cache cluster per
  member (``<group>-001``, ``<group>-002``, ...). Moto lists the member IDs but
  does not create the clusters, so DescribeCacheClusters returns
  CacheClusterNotFound and OpenTofu/Terraform fails after create.
  The provider creates the member clusters. When no engine version is given,
  the member clusters get the default version of the engine (AWS also chooses
  one); an empty version makes the OpenTofu/Terraform AWS provider fail.
- With cluster mode disabled, Moto ignores ``NumCacheClusters`` and creates
  only the primary unless ``ReplicasPerNodeGroup`` is set. The provider uses
  ``NumCacheClusters - 1`` replicas in that case, like AWS.
- In AWS, a deleted replication group disappears after deletion completes.
  Moto keeps it with status "deleting" forever, so OpenTofu/Terraform waits
  until it times out. The provider removes the group and its member clusters.
"""

import logging

from moto.elasticache.models import ElastiCacheBackend, ReplicationGroup, elasticache_backends

from localstack.aws.api import RequestContext, handler
from localstack.aws.api.elasticache import (
    CacheClusterMessage,
    CacheSubnetGroupInUse,
    CacheSubnetGroupNotFoundFault,
    DescribeCacheClustersMessage,
    ElasticacheApi,
    String,
)
from localstack.services.moto import call_moto
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch

LOG = logging.getLogger(__name__)

# parameters of create_replication_group that are copied to each member cluster
_SHARED_CLUSTER_PARAMS = (
    "cache_node_type",
    "engine",
    "engine_version",
    "cache_parameter_group_name",
    "cache_subnet_group_name",
    "cache_security_group_names",
    "security_group_ids",
    "preferred_maintenance_window",
    "port",
    "notification_topic_arn",
    "auto_minor_version_upgrade",
    "snapshot_retention_limit",
    "snapshot_window",
    "auth_token",
    "transit_encryption_enabled",
    "network_type",
    "ip_discovery",
    "log_delivery_configurations",
)

# Used only when the request has no EngineVersion. These are recent versions
# that AWS supports; they are not guaranteed to be the current AWS defaults.
DEFAULT_ENGINE_VERSIONS = {"valkey": "8.1", "redis": "7.1", "memcached": "1.6.22"}


@patch(ReplicationGroup._set_node_members_clusters_disabled)
def _set_node_members_clusters_disabled(fn, self: ReplicationGroup, *args, **kwargs):
    num_cache_clusters = kwargs.get("num_cache_clusters")
    if not kwargs.get("replicas_per_node_group") and num_cache_clusters:
        kwargs["replicas_per_node_group"] = max(int(num_cache_clusters) - 1, 0)
    return fn(self, *args, **kwargs)


@patch(ElastiCacheBackend.create_replication_group)
def _create_replication_group(fn, self: ElastiCacheBackend, **kwargs):
    group = fn(self, **kwargs)
    azs = kwargs.get("preferred_cache_cluster_azs") or []
    shared = {name: kwargs.get(name) for name in _SHARED_CLUSTER_PARAMS}
    shared["log_delivery_configurations"] = shared["log_delivery_configurations"] or []
    engine = (shared["engine"] or "redis").lower()
    shared["engine"] = engine
    if not shared["engine_version"]:
        shared["engine_version"] = DEFAULT_ENGINE_VERSIONS.get(engine, "")

    for index, cluster_id in enumerate(group.member_clusters):
        if cluster_id in self.cache_clusters:
            continue
        try:
            cluster = self.create_cache_cluster(
                cache_cluster_id=cluster_id,
                replication_group_id=group.replication_group_id,
                az_mode="single-az",
                preferred_availability_zone=azs[index] if index < len(azs) else None,
                num_cache_nodes=1,
                tags=None,
                snapshot_arns=None,
                snapshot_name=None,
                outpost_mode=None,
                preferred_outpost_arn=None,
                preferred_availability_zones=None,
                preferred_outpost_arns=None,
                cache_node_ids_to_remove=None,
                cache_node_ids_to_reboot=None,
                **shared,
            )
            # Moto records the group only for the "redis" engine, not for "valkey"
            cluster.replication_group_id = group.replication_group_id
        except Exception as e:
            # the group itself is valid; a missing member cluster must not fail the request
            LOG.warning(
                "Cannot create member cluster %s of replication group %s: %s",
                cluster_id,
                group.replication_group_id,
                e,
            )
    return group


@patch(ElastiCacheBackend.delete_replication_group)
def _delete_replication_group(
    fn, self: ElastiCacheBackend, replication_group_id: str, retain_primary_cluster=None
):
    primary_id = None
    members: list[str] = []
    if replication_group_id in self.replication_groups:
        existing = self.replication_groups[replication_group_id]
        primary_id = existing.primary_cluster_id
        members = list(existing.member_clusters)

    # raises ReplicationGroupNotFound when the group does not exist
    group = fn(self, replication_group_id, retain_primary_cluster)

    for cluster_id in members:
        if retain_primary_cluster and cluster_id == primary_id:
            # the retained primary is now a standalone cluster
            self.cache_clusters[cluster_id].replication_group_id = None
            continue
        self.cache_clusters.pop(cluster_id, None)

    # the response shows status "deleting"; afterwards the group no longer exists
    self.replication_groups.pop(replication_group_id, None)
    return group


class ElasticacheProvider(ElasticacheApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(elasticache_backends)

    @handler("DescribeCacheClusters", expand=False)
    def describe_cache_clusters(
        self, context: RequestContext, request: DescribeCacheClustersMessage
    ) -> CacheClusterMessage:
        result = call_moto(context)
        backend: ElastiCacheBackend = elasticache_backends[context.account_id][context.region]
        for cluster in result.get("CacheClusters") or []:
            stored = backend.cache_clusters.get(cluster.get("CacheClusterId"))
            group_id = getattr(stored, "replication_group_id", None)
            if group_id and not cluster.get("ReplicationGroupId"):
                cluster["ReplicationGroupId"] = group_id
        return result

    def delete_cache_subnet_group(
        self, context: RequestContext, cache_subnet_group_name: String, **kwargs
    ) -> None:
        backend: ElastiCacheBackend = elasticache_backends[context.account_id][context.region]
        if cache_subnet_group_name not in backend.cache_subnet_groups:
            raise CacheSubnetGroupNotFoundFault(
                f"CacheSubnetGroup {cache_subnet_group_name} not found."
            )
        in_use = [
            cluster.cache_cluster_id
            for cluster in backend.cache_clusters.values()
            if getattr(cluster, "cache_subnet_group_name", None) == cache_subnet_group_name
        ]
        if in_use:
            raise CacheSubnetGroupInUse(
                f"Cache subnet group {cache_subnet_group_name} is currently in use by a cache cluster."
            )
        del backend.cache_subnet_groups[cache_subnet_group_name]
