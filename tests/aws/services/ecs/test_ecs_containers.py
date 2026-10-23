"""ECS tasks run as Docker containers (issue #1, phase 2).

These tests start real containers. Set MOCKSY_TEST_ECS_IMAGE to an image with
``python3`` when the default image cannot be pulled (for example offline).
"""

import json
import os
import time
import urllib.request

import pytest

from localstack.testing.pytest import markers
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

IMAGE = os.environ.get("MOCKSY_TEST_ECS_IMAGE", "python:3.13-alpine")

# a small HTTP server that prints its configuration first
SERVER = (
    "import os, http.server;"
    "print('mode=' + os.environ.get('APP_MODE', '') + ' pw=' + os.environ.get('DB_PASSWORD', ''), flush=True);"
    "http.server.HTTPServer(('', 8080), http.server.SimpleHTTPRequestHandler).serve_forever()"
)

pytestmark = [
    markers.requires_docker,
    pytest.mark.skipif(not DOCKER_CLIENT.has_docker(), reason="needs Docker"),
]


@pytest.fixture
def subnet_id(aws_client):
    return aws_client.ec2.describe_subnets(
        Filters=[{"Name": "default-for-az", "Values": ["true"]}]
    )["Subnets"][0]["SubnetId"]


@pytest.fixture
def cluster(aws_client, cleanups):
    name = f"c-{short_uid()}"
    aws_client.ecs.create_cluster(clusterName=name)

    def _cleanup():
        for service in aws_client.ecs.list_services(cluster=name)["serviceArns"]:
            aws_client.ecs.delete_service(cluster=name, service=service, force=True)
        for task in aws_client.ecs.list_tasks(cluster=name)["taskArns"]:
            aws_client.ecs.stop_task(cluster=name, task=task)

    cleanups.append(_cleanup)
    return name


def _register(aws_client, command: str = SERVER, **container) -> str:
    family = f"td-{short_uid()}"
    definition = {
        "name": "web",
        "image": IMAGE,
        "essential": True,
        "command": ["python3", "-c", command],
        "portMappings": [{"containerPort": 8080}],
    }
    definition.update(container)
    aws_client.ecs.register_task_definition(
        family=family,
        requiresCompatibilities=["FARGATE"],
        networkMode="awsvpc",
        cpu="256",
        memory="512",
        containerDefinitions=[definition],
    )
    return family


def _describe(aws_client, cluster: str, task_arn: str) -> dict:
    return aws_client.ecs.describe_tasks(cluster=cluster, tasks=[task_arn])["tasks"][0]


def _wait_status(aws_client, cluster: str, task_arn: str, status: str) -> dict:
    def _check():
        task = _describe(aws_client, cluster, task_arn)
        assert task["lastStatus"] == status, task.get("stoppedReason")
        return task

    return retry(_check, retries=90, sleep=1)


def _task_ip(task: dict) -> str:
    return next(
        d["value"]
        for a in task["attachments"]
        for d in a["details"]
        if d["name"] == "privateIPv4Address"
    )


def _running_service_tasks(aws_client, cluster: str, service: str) -> list[str]:
    return aws_client.ecs.list_tasks(cluster=cluster, serviceName=service, desiredStatus="RUNNING")[
        "taskArns"
    ]


class TestEcsContainers:
    @markers.aws.only_localstack
    def test_run_task_starts_container(self, aws_client, cluster, subnet_id):
        secret_arn = aws_client.secretsmanager.create_secret(
            Name=f"s-{short_uid()}", SecretString=json.dumps({"password": "s3cret"})
        )["ARN"]
        group = f"/ecs/{short_uid()}"
        aws_client.logs.create_log_group(logGroupName=group)
        family = _register(
            aws_client,
            environment=[{"name": "APP_MODE", "value": "dev"}],
            secrets=[{"name": "DB_PASSWORD", "valueFrom": f"{secret_arn}:password::"}],
            logConfiguration={
                "logDriver": "awslogs",
                "options": {"awslogs-group": group, "awslogs-stream-prefix": "app"},
            },
        )
        task_arn = aws_client.ecs.run_task(
            cluster=cluster,
            taskDefinition=family,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet_id]}},
        )["tasks"][0]["taskArn"]

        task = _wait_status(aws_client, cluster, task_arn, "RUNNING")
        container = task["containers"][0]
        assert container["lastStatus"] == "RUNNING"
        assert container["runtimeId"]

        # the container serves HTTP on the task IP
        def _http():
            with urllib.request.urlopen(f"http://{_task_ip(task)}:8080/", timeout=5) as r:
                assert r.status == 200

        retry(_http, retries=20, sleep=1)

        # environment and secret reach the container, output reaches CloudWatch Logs
        task_id = task_arn.split("/")[-1]
        stream = f"app/web/{task_id}"

        def _logs():
            events = aws_client.logs.get_log_events(logGroupName=group, logStreamName=stream)[
                "events"
            ]
            assert "mode=dev pw=s3cret" in [e["message"] for e in events]

        retry(_logs, retries=20, sleep=1)

        stopping = aws_client.ecs.stop_task(cluster=cluster, task=task_arn, reason="test done")
        assert stopping["task"]["desiredStatus"] == "STOPPED"
        task = _wait_status(aws_client, cluster, task_arn, "STOPPED")
        assert task["stoppedReason"] == "test done"
        assert task["stopCode"] == "UserInitiated"
        assert not DOCKER_CLIENT.list_containers(filter=f"label=mocksy.ecs.task-arn={task_arn}")

        # stopping again does not change the task
        aws_client.ecs.stop_task(cluster=cluster, task=task_arn, reason="again")
        assert _describe(aws_client, cluster, task_arn)["stoppedReason"] == "test done"

    @markers.aws.only_localstack
    def test_essential_container_exit_stops_task(self, aws_client, cluster, subnet_id):
        family = _register(aws_client, command="import sys; sys.exit(3)")
        task_arn = aws_client.ecs.run_task(
            cluster=cluster,
            taskDefinition=family,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet_id]}},
        )["tasks"][0]["taskArn"]

        task = _wait_status(aws_client, cluster, task_arn, "STOPPED")
        assert task["stopCode"] == "EssentialContainerExited"
        assert task["containers"][0]["exitCode"] == 3

    @markers.aws.only_localstack
    def test_missing_secret_fails_task(self, aws_client, cluster, subnet_id):
        missing = f"arn:aws:secretsmanager:us-east-1:000000000000:secret:missing-{short_uid()}"
        family = _register(aws_client, secrets=[{"name": "X", "valueFrom": missing}])
        task_arn = aws_client.ecs.run_task(
            cluster=cluster,
            taskDefinition=family,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet_id]}},
        )["tasks"][0]["taskArn"]

        task = _wait_status(aws_client, cluster, task_arn, "STOPPED")
        assert task["stopCode"] == "TaskFailedToStart"
        assert task["stoppedReason"].startswith("ResourceInitializationError")

    @markers.aws.only_localstack
    def test_service_keeps_desired_count(self, aws_client, cluster, subnet_id):
        family = _register(aws_client)
        aws_client.ecs.create_service(
            cluster=cluster,
            serviceName="api",
            taskDefinition=family,
            desiredCount=2,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet_id]}},
        )

        def _count(expected: int) -> list[str]:
            tasks = _running_service_tasks(aws_client, cluster, "api")
            assert len(tasks) == expected
            if tasks:
                described = aws_client.ecs.describe_tasks(cluster=cluster, tasks=tasks)["tasks"]
                assert all(t["lastStatus"] == "RUNNING" for t in described)
            service = aws_client.ecs.describe_services(cluster=cluster, services=["api"])[
                "services"
            ][0]
            assert service["runningCount"] == expected
            return tasks

        tasks = retry(lambda: _count(2), retries=60, sleep=1)

        # a stopped task is replaced
        aws_client.ecs.stop_task(cluster=cluster, task=tasks[0])
        replaced = retry(lambda: _count(2), retries=60, sleep=1)
        assert tasks[0] not in replaced

        # scale up and down
        aws_client.ecs.update_service(cluster=cluster, service="api", desiredCount=3)
        retry(lambda: _count(3), retries=60, sleep=1)
        aws_client.ecs.update_service(cluster=cluster, service="api", desiredCount=0)
        retry(lambda: _count(0), retries=60, sleep=1)

    @markers.aws.only_localstack
    def test_service_backs_off_when_tasks_fail(self, aws_client, cluster, subnet_id):
        family = _register(aws_client, image=f"mocksy-test/missing-{short_uid()}:1")
        aws_client.ecs.create_service(
            cluster=cluster,
            serviceName="broken",
            taskDefinition=family,
            desiredCount=1,
            launchType="FARGATE",
            networkConfiguration={"awsvpcConfiguration": {"subnets": [subnet_id]}},
        )

        def _stopped() -> list[dict]:
            arns = aws_client.ecs.list_tasks(cluster=cluster, desiredStatus="STOPPED")["taskArns"]
            assert arns
            return aws_client.ecs.describe_tasks(cluster=cluster, tasks=arns)["tasks"]

        first = retry(_stopped, retries=30, sleep=1)
        assert first[0]["stoppedReason"].startswith("CannotPullContainerError")

        # without backoff a new task would start every monitor interval
        time.sleep(8)
        assert len(_stopped()) <= 3
