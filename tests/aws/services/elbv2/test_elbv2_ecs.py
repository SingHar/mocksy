"""ECS services behind an Application Load Balancer (issue #14).

These tests start ECS task containers. Set MOCKSY_TEST_ECS_IMAGE to an image
with ``python3`` when the default image cannot be pulled.
"""

import os

import pytest
import requests

from localstack import config
from localstack.testing.pytest import markers
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

IMAGE = os.environ.get("MOCKSY_TEST_ECS_IMAGE", "python:3.13-alpine")

pytestmark = [
    markers.requires_docker,
    pytest.mark.skipif(not DOCKER_CLIENT.has_docker(), reason="needs Docker"),
]

# answers with the container's host name; /health fails when the file /tmp/sick exists
SERVER = """
import http.server, os, socket
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" and os.path.exists("/tmp/sick"):
            self.send_response(500); self.end_headers(); return
        body = socket.gethostname().encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass
http.server.ThreadingHTTPServer(("", 8080), H).serve_forever()
"""


@pytest.fixture
def stack(aws_client, cleanups):
    """An ALB with a listener and target group, and an ECS service with 2 tasks behind it."""
    ec2, elbv2, ecs = aws_client.ec2, aws_client.elbv2, aws_client.ecs
    vpc_id = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0][
        "VpcId"
    ]
    subnets = [
        s["SubnetId"]
        for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    ][:2]
    suffix = short_uid()
    lb = elbv2.create_load_balancer(Name=f"lb-{suffix}", Subnets=subnets)["LoadBalancers"][0]
    cleanups.append(lambda: elbv2.delete_load_balancer(LoadBalancerArn=lb["LoadBalancerArn"]))
    tg_arn = elbv2.create_target_group(
        Name=f"tg-{suffix}",
        Protocol="HTTP",
        Port=8080,
        VpcId=vpc_id,
        TargetType="ip",
        HealthCheckPath="/health",
        HealthCheckIntervalSeconds=5,
        HealthCheckTimeoutSeconds=2,
        HealthyThresholdCount=2,
        UnhealthyThresholdCount=2,
    )["TargetGroups"][0]["TargetGroupArn"]
    cleanups.append(lambda: elbv2.delete_target_group(TargetGroupArn=tg_arn))
    elbv2.create_listener(
        LoadBalancerArn=lb["LoadBalancerArn"],
        Protocol="HTTP",
        Port=80,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": tg_arn}],
    )

    cluster = f"c-{suffix}"
    ecs.create_cluster(clusterName=cluster)
    ecs.register_task_definition(
        family=f"td-{suffix}",
        requiresCompatibilities=["FARGATE"],
        networkMode="awsvpc",
        cpu="256",
        memory="512",
        containerDefinitions=[
            {
                "name": "web",
                "image": IMAGE,
                "essential": True,
                "command": ["python3", "-c", SERVER],
                "portMappings": [{"containerPort": 8080}],
            }
        ],
    )
    ecs.create_service(
        cluster=cluster,
        serviceName="web",
        taskDefinition=f"td-{suffix}",
        desiredCount=2,
        launchType="FARGATE",
        networkConfiguration={"awsvpcConfiguration": {"subnets": subnets}},
        loadBalancers=[{"targetGroupArn": tg_arn, "containerName": "web", "containerPort": 8080}],
        healthCheckGracePeriodSeconds=0,
    )
    cleanups.append(lambda: ecs.delete_service(cluster=cluster, service="web", force=True))
    return lb, tg_arn, cluster


def _targets(aws_client, tg_arn: str) -> list[dict]:
    return aws_client.elbv2.describe_target_health(TargetGroupArn=tg_arn)[
        "TargetHealthDescriptions"
    ]


def _healthy_ips(aws_client, tg_arn: str, count: int) -> set[str]:
    def _check():
        healthy = {
            t["Target"]["Id"]
            for t in _targets(aws_client, tg_arn)
            if t["TargetHealth"]["State"] == "healthy"
        }
        assert len(healthy) == count
        return healthy

    return retry(_check, retries=90, sleep=1)


def _get(lb: dict, path: str = "/") -> requests.Response:
    return requests.get(
        config.internal_service_url() + path, headers={"Host": lb["DNSName"]}, timeout=10
    )


def _task_with_ip(aws_client, cluster: str, ip: str) -> str:
    arns = aws_client.ecs.list_tasks(cluster=cluster, serviceName="web", desiredStatus="RUNNING")[
        "taskArns"
    ]
    for task in aws_client.ecs.describe_tasks(cluster=cluster, tasks=arns)["tasks"]:
        for attachment in task["attachments"]:
            for detail in attachment["details"]:
                if detail["name"] == "privateIPv4Address" and detail["value"] == ip:
                    return task["taskArn"]
    raise AssertionError(f"no running task with IP {ip}")


class TestElbv2Ecs:
    @markers.aws.only_localstack
    def test_service_behind_load_balancer(self, aws_client, stack):
        lb, tg_arn, cluster = stack
        ips = _healthy_ips(aws_client, tg_arn, 2)

        hosts = {_get(lb).text for _ in range(6)}
        assert len(hosts) == 2

        # a stopped task leaves the target group; its replacement joins it
        stopped_ip = sorted(ips)[0]
        aws_client.ecs.stop_task(
            cluster=cluster, task=_task_with_ip(aws_client, cluster, stopped_ip)
        )

        def _replaced():
            current = _healthy_ips(aws_client, tg_arn, 2)
            assert stopped_ip not in current
            assert stopped_ip not in {t["Target"]["Id"] for t in _targets(aws_client, tg_arn)}

        retry(_replaced, retries=90, sleep=1)
        assert all(_get(lb).status_code == 200 for _ in range(4))

    @markers.aws.only_localstack
    def test_unhealthy_task_is_replaced(self, aws_client, stack):
        lb, tg_arn, cluster = stack
        ips = _healthy_ips(aws_client, tg_arn, 2)
        sick_ip = sorted(ips)[0]
        sick_task = _task_with_ip(aws_client, cluster, sick_ip)
        container = aws_client.ecs.describe_tasks(cluster=cluster, tasks=[sick_task])["tasks"][0][
            "containers"
        ][0]["runtimeId"]
        DOCKER_CLIENT.exec_in_container(container, ["python3", "-c", "open('/tmp/sick','w')"])

        def _stopped():
            task = aws_client.ecs.describe_tasks(cluster=cluster, tasks=[sick_task])["tasks"][0]
            assert task["desiredStatus"] == "STOPPED"
            assert task["stoppedReason"].startswith("Task failed ELB health checks")

        retry(_stopped, retries=60, sleep=1)
        current = _healthy_ips(aws_client, tg_arn, 2)
        assert sick_ip not in current

    @markers.aws.only_localstack
    def test_scale_on_request_count_per_target(self, aws_client, stack, monkeypatch, cleanups):
        monkeypatch.setattr(config, "ELBV2_METRICS_INTERVAL", 1)
        monkeypatch.setattr(config, "APPLICATION_AUTOSCALING_INTERVAL", 0.5)
        monkeypatch.setattr(config, "APPLICATION_AUTOSCALING_METRIC_PERIOD", 60)
        lb, tg_arn, cluster = stack
        _healthy_ips(aws_client, tg_arn, 2)

        resource_id = f"service/{cluster}/web"
        autoscaling = aws_client.application_autoscaling
        autoscaling.register_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
            MinCapacity=1,
            MaxCapacity=3,
        )
        cleanups.append(
            lambda: autoscaling.deregister_scalable_target(
                ServiceNamespace="ecs",
                ResourceId=resource_id,
                ScalableDimension="ecs:service:DesiredCount",
            )
        )
        label = lb["LoadBalancerArn"].split(":loadbalancer/", 1)[1] + "/" + tg_arn.split(":", 5)[-1]
        autoscaling.put_scaling_policy(
            PolicyName="requests",
            ServiceNamespace="ecs",
            ResourceId=resource_id,
            ScalableDimension="ecs:service:DesiredCount",
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": 5,
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "ALBRequestCountPerTarget",
                    "ResourceLabel": label,
                },
                "ScaleOutCooldown": 0,
                "ScaleInCooldown": 3600,
            },
        )
        # 30 requests for 2 targets: 15 per target, target 5 → 6 tasks, at most 3
        for _ in range(30):
            assert _get(lb).status_code == 200

        def _scaled_out():
            service = aws_client.ecs.describe_services(cluster=cluster, services=["web"])[
                "services"
            ][0]
            assert service["desiredCount"] == 3

        retry(_scaled_out, retries=30, sleep=1)
        _healthy_ips(aws_client, tg_arn, 3)
