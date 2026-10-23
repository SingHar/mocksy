import pytest

from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid


class TestElasticache:
    @markers.aws.unknown
    def test_replication_group_creates_member_clusters(self, aws_client):
        group_id = f"g-{short_uid()}"
        aws_client.elasticache.create_replication_group(
            ReplicationGroupId=group_id,
            ReplicationGroupDescription="test",
            Engine="valkey",
            CacheNodeType="cache.t4g.micro",
            NumCacheClusters=2,
        )
        group = aws_client.elasticache.describe_replication_groups(ReplicationGroupId=group_id)[
            "ReplicationGroups"
        ][0]
        assert group["MemberClusters"] == [f"{group_id}-001", f"{group_id}-002"]

        for cluster_id in group["MemberClusters"]:
            cluster = aws_client.elasticache.describe_cache_clusters(CacheClusterId=cluster_id)[
                "CacheClusters"
            ][0]
            assert cluster["ReplicationGroupId"] == group_id
            assert cluster["EngineVersion"]

        aws_client.elasticache.delete_replication_group(ReplicationGroupId=group_id)
        with pytest.raises(aws_client.elasticache.exceptions.ReplicationGroupNotFoundFault):
            aws_client.elasticache.describe_replication_groups(ReplicationGroupId=group_id)
        with pytest.raises(aws_client.elasticache.exceptions.CacheClusterNotFoundFault):
            aws_client.elasticache.describe_cache_clusters(CacheClusterId=f"{group_id}-001")

    @markers.aws.unknown
    def test_delete_cache_subnet_group(self, aws_client):
        subnet_id = aws_client.ec2.describe_subnets()["Subnets"][0]["SubnetId"]
        name = f"sg-{short_uid()}"
        aws_client.elasticache.create_cache_subnet_group(
            CacheSubnetGroupName=name,
            CacheSubnetGroupDescription="test",
            SubnetIds=[subnet_id],
        )
        aws_client.elasticache.delete_cache_subnet_group(CacheSubnetGroupName=name)

        with pytest.raises(aws_client.elasticache.exceptions.CacheSubnetGroupNotFoundFault):
            aws_client.elasticache.delete_cache_subnet_group(CacheSubnetGroupName=name)

    @markers.aws.unknown
    def test_delete_cache_subnet_group_in_use(self, aws_client):
        subnet_id = aws_client.ec2.describe_subnets()["Subnets"][0]["SubnetId"]
        name = f"sg-{short_uid()}"
        group_id = f"g-{short_uid()}"
        aws_client.elasticache.create_cache_subnet_group(
            CacheSubnetGroupName=name,
            CacheSubnetGroupDescription="test",
            SubnetIds=[subnet_id],
        )
        aws_client.elasticache.create_replication_group(
            ReplicationGroupId=group_id,
            ReplicationGroupDescription="test",
            Engine="valkey",
            CacheNodeType="cache.t4g.micro",
            NumCacheClusters=1,
            CacheSubnetGroupName=name,
        )
        with pytest.raises(aws_client.elasticache.exceptions.CacheSubnetGroupInUse):
            aws_client.elasticache.delete_cache_subnet_group(CacheSubnetGroupName=name)

        aws_client.elasticache.delete_replication_group(ReplicationGroupId=group_id)
        aws_client.elasticache.delete_cache_subnet_group(CacheSubnetGroupName=name)
