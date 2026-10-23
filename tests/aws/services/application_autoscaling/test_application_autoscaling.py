"""Application Auto Scaling (issue #5).

The API tests run without Docker. The scaling tests start ECS task containers;
set MOCKSY_TEST_ECS_IMAGE to an image with ``python3`` when the default image
cannot be pulled.
"""

import os
import time
from datetime import UTC, datetime

import pytest

from localstack.testing.pytest import markers
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

IMAGE = os.environ.get("MOCKSY_TEST_ECS_IMAGE", "python:3.13-alpine")
DIMENSION = "ecs:service:DesiredCount"

requires_docker = [
    markers.requires_docker,
    pytest.mark.skipif(not DOCKER_CLIENT.has_docker(), reason="needs Docker"),
]


@pytest.fixture
def ecs_service(aws_client, cleanups):
    """An ECS Fargate service with one task; returns (cluster, service, resource ID)."""
    cluster = f"c-{short_uid()}"
    family = f"td-{short_uid()}"
    aws_client.ecs.create_cluster(clusterName=cluster)
    aws_client.ecs.register_task_definition(
        family=family,
        requiresCompatibilities=["FARGATE"],
        networkMode="awsvpc",
        cpu="256",
        memory="512",
        containerDefinitions=[
            {
                "name": "worker",
                "image": IMAGE,
                "essential": True,
                "command": ["python3", "-c", "import time; time.sleep(3600)"],
            }
        ],
    )
    subnet = aws_client.ec2.describe_subnets(
        Filters=[{"Name": "default-for-az", "Values": ["true"]}]
    )["Subnets"][0]["SubnetId"]
    aws_client.ecs.create_service(
        cluster=cluster,
        serviceName="worker",
        taskDefinition=family,
        desiredCount=1,
        launchType="FARGATE",
        networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet]}},
    )

    def _cleanup():
        aws_client.ecs.delete_service(cluster=cluster, service="worker", force=True)

    cleanups.append(_cleanup)
    return cluster, "worker", f"service/{cluster}/worker"


@pytest.fixture
def scalable_target(aws_client, ecs_service, cleanups):
    _, _, resource_id = ecs_service

    def _register(min_capacity: int = 1, max_capacity: int = 4) -> str:
        aws_client.application_autoscaling.register_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            MinCapacity=min_capacity,
            MaxCapacity=max_capacity,
        )
        cleanups.append(
            lambda: aws_client.application_autoscaling.deregister_scalable_target(
                ServiceNamespace="ecs", ResourceId=resource_id, ScalableDimension=DIMENSION
            )
        )
        return resource_id

    return _register


def _desired(aws_client, cluster: str, service: str) -> int:
    return aws_client.ecs.describe_services(cluster=cluster, services=[service])["services"][0][
        "desiredCount"
    ]


def _put_metric(aws_client, namespace: str, name: str, value: float, dimensions: list) -> None:
    aws_client.cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=[
            {
                "MetricName": name,
                "Dimensions": dimensions,
                "Value": value,
                "Timestamp": datetime.now(tz=UTC),
                "StorageResolution": 1,
            }
        ],
    )


class TestApplicationAutoscalingApi:
    @markers.aws.unknown
    def test_target_and_policies(self, aws_client, ecs_service, scalable_target):
        resource_id = scalable_target(min_capacity=1, max_capacity=5)
        targets = aws_client.application_autoscaling.describe_scalable_targets(
            ServiceNamespace="ecs", ResourceIds=[resource_id]
        )["ScalableTargets"]
        assert targets[0]["MinCapacity"] == 1
        assert targets[0]["MaxCapacity"] == 5

        aws_client.application_autoscaling.put_scaling_policy(
            PolicyName="cpu",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": 60,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
                },
            },
        )
        aws_client.application_autoscaling.put_scaling_policy(
            PolicyName="step",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            PolicyType="StepScaling",
            StepScalingPolicyConfiguration={
                "AdjustmentType": "ChangeInCapacity",
                "StepAdjustments": [{"MetricIntervalLowerBound": 0, "ScalingAdjustment": 1}],
            },
        )
        policies = aws_client.application_autoscaling.describe_scaling_policies(
            ServiceNamespace="ecs", ResourceId=resource_id
        )["ScalingPolicies"]
        assert sorted(p["PolicyName"] for p in policies) == ["cpu", "step"]

        activities = aws_client.application_autoscaling.describe_scaling_activities(
            ServiceNamespace="ecs", ResourceId=resource_id
        )["ScalingActivities"]
        assert activities == []

        for name in ("cpu", "step"):
            aws_client.application_autoscaling.delete_scaling_policy(
                PolicyName=name,
                ServiceNamespace="ecs",
                ResourceId=resource_id,
                ScalableDimension=DIMENSION,
            )


@pytest.mark.usefixtures("scaling_fast")
class TestApplicationAutoscalingScaling:
    pytestmark = requires_docker

    @pytest.fixture
    def scaling_fast(self, monkeypatch):
        from localstack import config

        monkeypatch.setattr(config, "APPLICATION_AUTOSCALING_INTERVAL", 0.5)
        monkeypatch.setattr(config, "APPLICATION_AUTOSCALING_METRIC_PERIOD", 1)

    @markers.aws.only_localstack
    def test_target_tracking_on_queue_depth(self, aws_client, ecs_service, scalable_target):
        cluster, service, _ = ecs_service
        resource_id = scalable_target(min_capacity=1, max_capacity=4)
        namespace, metric = f"Mocksy/{short_uid()}", "QueueDepth"
        dimensions = [{"Name": "Queue", "Value": "default"}]
        aws_client.application_autoscaling.put_scaling_policy(
            PolicyName="queue",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": 10,
                "CustomizedMetricSpecification": {
                    "Namespace": namespace,
                    "MetricName": metric,
                    "Dimensions": dimensions,
                    "Statistic": "Maximum",
                },
                "ScaleOutCooldown": 0,
                "ScaleInCooldown": 0,
            },
        )

        # 35 messages for 1 task, 10 per task: 4 tasks (the maximum)
        def _scaled_out():
            _put_metric(aws_client, namespace, metric, 35, dimensions)
            assert _desired(aws_client, cluster, service) == 4

        retry(_scaled_out, retries=30, sleep=1)

        # 5 messages for 4 tasks: 2 tasks
        def _scaled_in():
            _put_metric(aws_client, namespace, metric, 5, dimensions)
            assert _desired(aws_client, cluster, service) == 2

        retry(_scaled_in, retries=30, sleep=1)

        # 0 messages: the minimum, 1 task
        def _at_minimum():
            _put_metric(aws_client, namespace, metric, 0, dimensions)
            assert _desired(aws_client, cluster, service) == 1

        retry(_at_minimum, retries=30, sleep=1)

        activities = aws_client.application_autoscaling.describe_scaling_activities(
            ServiceNamespace="ecs", ResourceId=resource_id
        )["ScalingActivities"]
        assert [a["Description"] for a in activities[:3]] == [
            "Setting desired count to 1.",
            "Setting desired count to 2.",
            "Setting desired count to 4.",
        ]
        assert all(a["StatusCode"] == "Successful" for a in activities)

    @markers.aws.only_localstack
    def test_step_scaling_on_alarm(self, aws_client, ecs_service, scalable_target):
        cluster, service, _ = ecs_service
        resource_id = scalable_target(min_capacity=1, max_capacity=5)
        policy_arn = aws_client.application_autoscaling.put_scaling_policy(
            PolicyName="step-out",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            PolicyType="StepScaling",
            StepScalingPolicyConfiguration={
                "AdjustmentType": "ChangeInCapacity",
                "Cooldown": 3600,
                "StepAdjustments": [
                    {
                        "MetricIntervalLowerBound": 0,
                        "MetricIntervalUpperBound": 50,
                        "ScalingAdjustment": 1,
                    },
                    {"MetricIntervalLowerBound": 50, "ScalingAdjustment": 2},
                ],
            },
        )["PolicyARN"]
        namespace = f"Mocksy/{short_uid()}"
        alarm = f"high-{short_uid()}"
        aws_client.cloudwatch.put_metric_alarm(
            AlarmName=alarm,
            Namespace=namespace,
            MetricName="Backlog",
            Statistic="Maximum",
            Period=60,
            EvaluationPeriods=1,
            Threshold=100,
            ComparisonOperator="GreaterThanThreshold",
            AlarmActions=[policy_arn],
        )
        # 175 is 75 above the threshold: the second step, +2 tasks
        _put_metric(aws_client, namespace, "Backlog", 175, [])
        aws_client.cloudwatch.set_alarm_state(
            AlarmName=alarm, StateValue="ALARM", StateReason="test"
        )

        retry(lambda: _assert_equal(_desired(aws_client, cluster, service), 3), retries=30, sleep=1)

        # the cooldown stops a second change while the alarm stays in ALARM
        time.sleep(3)
        assert _desired(aws_client, cluster, service) == 3

    @markers.aws.only_localstack
    def test_ecs_utilization_metrics(self, aws_client, ecs_service, scalable_target):
        cluster, service, _ = ecs_service
        scalable_target()

        def _metrics():
            metrics = aws_client.cloudwatch.list_metrics(
                Namespace="AWS/ECS",
                Dimensions=[
                    {"Name": "ClusterName", "Value": cluster},
                    {"Name": "ServiceName", "Value": service},
                ],
            )["Metrics"]
            assert {m["MetricName"] for m in metrics} >= {"CPUUtilization", "MemoryUtilization"}

        retry(_metrics, retries=60, sleep=1)


def _assert_equal(actual, expected):
    assert actual == expected


class TestApplicationAutoscalingTags:
    @markers.aws.unknown
    def test_tags(self, aws_client, ecs_service, cleanups):
        _, _, resource_id = ecs_service
        arn = aws_client.application_autoscaling.register_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension=DIMENSION,
            MinCapacity=1,
            MaxCapacity=2,
            Tags={"env": "dev"},
        )["ScalableTargetARN"]
        cleanups.append(
            lambda: aws_client.application_autoscaling.deregister_scalable_target(
                ServiceNamespace="ecs", ResourceId=resource_id, ScalableDimension=DIMENSION
            )
        )
        client = aws_client.application_autoscaling
        assert client.list_tags_for_resource(ResourceARN=arn)["Tags"] == {"env": "dev"}
        client.tag_resource(ResourceARN=arn, Tags={"team": "api"})
        client.untag_resource(ResourceARN=arn, TagKeys=["env"])
        assert client.list_tags_for_resource(ResourceARN=arn)["Tags"] == {"team": "api"}
