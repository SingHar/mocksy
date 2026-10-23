from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid


def _default_subnet(aws_client) -> dict:
    return aws_client.ec2.describe_subnets(
        Filters=[{"Name": "default-for-az", "Values": ["true"]}]
    )["Subnets"][0]


class TestEcs:
    @markers.aws.unknown
    def test_fargate_service_lifecycle(self, aws_client, cleanups):
        cluster_name = f"c-{short_uid()}"
        family = f"td-{short_uid()}"
        aws_client.ecs.create_cluster(clusterName=cluster_name)
        cleanups.append(lambda: aws_client.ecs.delete_cluster(cluster=cluster_name))

        aws_client.ecs.register_task_definition(
            family=family,
            requiresCompatibilities=["FARGATE"],
            networkMode="awsvpc",
            cpu="256",
            memory="512",
            containerDefinitions=[{"name": "api", "image": "nginx", "essential": True}],
        )

        subnet = _default_subnet(aws_client)
        service = aws_client.ecs.create_service(
            cluster=cluster_name,
            serviceName="api",
            taskDefinition=family,
            desiredCount=2,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet["SubnetId"]]}},
        )["service"]
        assert service["status"] == "ACTIVE"
        assert service["desiredCount"] == 2

        service = aws_client.ecs.update_service(
            cluster=cluster_name, service="api", desiredCount=0
        )["service"]
        assert service["desiredCount"] == 0
        aws_client.ecs.delete_service(cluster=cluster_name, service="api", force=True)

    @markers.aws.unknown
    def test_security_groups_optional(self, aws_client, cleanups):
        """securityGroups is optional in AWS; the configuration is shown as it was sent."""
        cluster_name = f"c-{short_uid()}"
        family = f"td-{short_uid()}"
        aws_client.ecs.create_cluster(clusterName=cluster_name)
        cleanups.append(lambda: aws_client.ecs.delete_cluster(cluster=cluster_name))
        aws_client.ecs.register_task_definition(
            family=family,
            requiresCompatibilities=["FARGATE"],
            networkMode="awsvpc",
            cpu="256",
            memory="512",
            containerDefinitions=[{"name": "api", "image": "nginx", "essential": True}],
        )
        subnet_id = _default_subnet(aws_client)["SubnetId"]
        network = {"awsvpcConfiguration": {"subnets": [subnet_id]}}

        service = aws_client.ecs.create_service(
            cluster=cluster_name,
            serviceName="api",
            taskDefinition=family,
            desiredCount=1,
            launchType="FARGATE",
            networkConfiguration=network,
        )["service"]
        cleanups.append(
            lambda: aws_client.ecs.delete_service(cluster=cluster_name, service="api", force=True)
        )
        assert not service["networkConfiguration"]["awsvpcConfiguration"].get("securityGroups")

        tasks = aws_client.ecs.run_task(
            cluster=cluster_name,
            taskDefinition=family,
            launchType="FARGATE",
            networkConfiguration=network,
        )["tasks"]
        assert len(tasks) == 1
