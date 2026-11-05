"""ElastiCache nodes run as Docker containers (issue #3, phase 2).

These tests start real containers from ``ELASTICACHE_VALKEY_IMAGE`` and
``ELASTICACHE_REDIS_IMAGE`` (defaults ``valkey/valkey:{major}``, ``redis:{major}``).
"""

import pytest
import redis

from localstack.testing.pytest import markers
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

pytestmark = [
    markers.requires_docker,
    pytest.mark.skipif(not DOCKER_CLIENT.has_docker(), reason="needs Docker"),
]

TOKEN = "a-test-auth-token-1234"


def _client(endpoint: dict, password: str | None = TOKEN, tls: bool = False) -> redis.Redis:
    # the endpoint host is localhost.localstack.cloud; connect to it on this machine
    return redis.Redis(
        host="127.0.0.1",
        port=endpoint["Port"],
        password=password,
        ssl=tls,
        ssl_cert_reqs=None,
        socket_timeout=5,
    )


def _wait_group(aws_client, group_id: str) -> dict:
    def _check():
        group = aws_client.elasticache.describe_replication_groups(ReplicationGroupId=group_id)[
            "ReplicationGroups"
        ][0]
        assert group["Status"] in ("available", "create-failed")
        return group

    group = retry(_check, retries=120, sleep=1)
    assert group["Status"] == "available"
    return group


@pytest.fixture
def create_group(aws_client):
    created = []

    def _create(**kwargs) -> str:
        group_id = kwargs.setdefault("ReplicationGroupId", f"g-{short_uid()}")
        kwargs.setdefault("ReplicationGroupDescription", "test")
        kwargs.setdefault("Engine", "valkey")
        kwargs.setdefault("EngineVersion", "8.1")
        kwargs.setdefault("CacheNodeType", "cache.t4g.micro")
        aws_client.elasticache.create_replication_group(**kwargs)
        created.append(group_id)
        return group_id

    yield _create

    for group_id in created:
        try:
            aws_client.elasticache.delete_replication_group(ReplicationGroupId=group_id)
        except Exception:
            pass


def _containers_of(arn: str) -> list:
    return DOCKER_CLIENT.list_containers(filter=f"label=mocksy.resource.arn={arn}")


class TestElasticacheContainers:
    @markers.aws.only_localstack
    def test_replication_group_with_replica(self, aws_client, create_group):
        group_id = create_group(NumCacheClusters=2, AuthToken=TOKEN)
        status = aws_client.elasticache.describe_replication_groups(ReplicationGroupId=group_id)[
            "ReplicationGroups"
        ][0]["Status"]
        assert status == "creating"

        group = _wait_group(aws_client, group_id)
        node_group = group["NodeGroups"][0]
        primary, reader = node_group["PrimaryEndpoint"], node_group["ReaderEndpoint"]
        assert primary["Address"] == "localhost.localstack.cloud"
        # the group's port (default 6379) keeps OpenTofu/Terraform plans stable
        assert primary["Port"] == 6379
        assert reader == primary
        members = {m["CurrentRole"]: m["ReadEndpoint"] for m in node_group["NodeGroupMembers"]}
        assert members["primary"]["Port"] == 6379
        replica = members["replica"]
        assert replica["Port"] != 6379

        _client(primary).set("greeting", "hello")

        def _replicated():
            assert _client(replica).get("greeting") == b"hello"

        retry(_replicated, retries=20, sleep=0.5)

        with pytest.raises(redis.exceptions.ReadOnlyError):
            _client(replica).set("greeting", "changed")
        assert _client(reader).get("greeting") == b"hello"
        with pytest.raises(redis.exceptions.AuthenticationError):
            _client(primary, password="wrong-token-123456").ping()

        for cluster_id in group["MemberClusters"]:
            cluster = aws_client.elasticache.describe_cache_clusters(CacheClusterId=cluster_id)[
                "CacheClusters"
            ][0]
            assert cluster["CacheClusterStatus"] == "available"

        aws_client.elasticache.delete_replication_group(ReplicationGroupId=group_id)
        assert not _containers_of(group["ARN"])

    @markers.aws.only_localstack
    def test_group_port(self, aws_client, create_group):
        group_id = create_group(NumCacheClusters=1, Port=4555)
        endpoint = _wait_group(aws_client, group_id)["NodeGroups"][0]["PrimaryEndpoint"]
        assert endpoint["Port"] == 4555
        assert _client(endpoint, password=None).ping()

    @markers.aws.only_localstack
    def test_transit_encryption(self, aws_client, create_group):
        group_id = create_group(NumCacheClusters=1, AuthToken=TOKEN, TransitEncryptionEnabled=True)
        endpoint = _wait_group(aws_client, group_id)["NodeGroups"][0]["PrimaryEndpoint"]

        client = _client(endpoint, tls=True)
        client.set("secure", "yes")
        assert client.get("secure") == b"yes"
        with pytest.raises(redis.exceptions.ConnectionError):
            _client(endpoint, tls=False).ping()

    @markers.aws.only_localstack
    def test_group_without_auth_token(self, aws_client, create_group):
        group_id = create_group(Engine="redis", EngineVersion="7.1", NumCacheClusters=1)
        endpoint = _wait_group(aws_client, group_id)["NodeGroups"][0]["PrimaryEndpoint"]
        assert _client(endpoint, password=None).ping()

    @markers.aws.only_localstack
    def test_standalone_cache_cluster(self, aws_client):
        cluster_id = f"c-{short_uid()}"
        aws_client.elasticache.create_cache_cluster(
            CacheClusterId=cluster_id,
            Engine="redis",
            EngineVersion="7.1",
            CacheNodeType="cache.t4g.micro",
            NumCacheNodes=1,
        )
        try:

            def _available():
                cluster = aws_client.elasticache.describe_cache_clusters(
                    CacheClusterId=cluster_id, ShowCacheNodeInfo=True
                )["CacheClusters"][0]
                assert cluster["CacheClusterStatus"] == "available"
                return cluster

            cluster = retry(_available, retries=60, sleep=1)
            endpoint = cluster["CacheNodes"][0]["Endpoint"]
            assert _client(endpoint, password=None).ping()
            arn = cluster["ARN"]
        finally:
            aws_client.elasticache.delete_cache_cluster(CacheClusterId=cluster_id)
        assert not _containers_of(arn)

    @markers.aws.only_localstack
    def test_delete_while_creating(self, aws_client, create_group):
        group_id = create_group(NumCacheClusters=2)
        arn = aws_client.elasticache.describe_replication_groups(ReplicationGroupId=group_id)[
            "ReplicationGroups"
        ][0]["ARN"]
        aws_client.elasticache.delete_replication_group(ReplicationGroupId=group_id)

        def _gone():
            assert not _containers_of(arn)

        retry(_gone, retries=30, sleep=1)
