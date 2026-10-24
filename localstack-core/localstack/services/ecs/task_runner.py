"""Runs ECS tasks as Docker containers (issue #1, phase 2).

Moto stores ECS state (clusters, task definitions, services, tasks). This module
adds the behaviour that Moto does not have:

- RunTask and StartTask start one Docker container for each container definition.
- StopTask stops the containers.
- A background loop checks the containers. When an essential container exits,
  the task stops, as in AWS.
- The same loop keeps the number of running tasks of each ACTIVE service equal
  to its ``desiredCount`` and replaces tasks that stopped.
- Container output goes to CloudWatch Logs when the ``awslogs`` log driver is set.
- ``secrets`` (Secrets Manager or SSM Parameter Store) are resolved when the
  container starts.

When Docker is not available, or ``ECS_RUN_CONTAINERS=0``, tasks are recorded
only, as in phase 1.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from localstack import config
from localstack.aws.connect import connect_to
from localstack.utils.container_networking import (
    get_endpoint_for_network,
    get_main_container_network,
)
from localstack.utils.docker_utils import DOCKER_CLIENT

LOG = logging.getLogger(__name__)

LABEL_MANAGED = "mocksy.ecs.managed"
LABEL_TASK_ARN = "mocksy.ecs.task-arn"
LABEL_CONTAINER = "mocksy.ecs.container-name"

# group prefix that AWS (and Moto) use for tasks that belong to a service
SERVICE_GROUP_PREFIX = "service:"


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _container_name(cluster: str, task_id: str, container: str) -> str:
    raw = f"mocksy-ecs-{cluster}-{task_id[:12]}-{container}"
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", raw)[:128]


class TaskStartError(Exception):
    """A task cannot start. ``stop_code`` and the message go to the task, as in AWS."""

    def __init__(self, message: str, stop_code: str = "TaskFailedToStart"):
        super().__init__(message)
        self.stop_code = stop_code


@dataclass
class ContainerRecord:
    """One container of a task. The attribute names match the ECS ``Container`` shape,
    so Moto's response serializer can return it from DescribeTasks."""

    container_arn: str
    task_arn: str
    name: str
    image: str
    essential: bool = True
    last_status: str = "PENDING"
    exit_code: int | None = None
    reason: str | None = None
    runtime_id: str | None = None
    health_status: str = "UNKNOWN"
    cpu: str | None = None
    memory: str | None = None
    network_interfaces: list[dict[str, str]] = field(default_factory=list)
    network_bindings: list[dict[str, Any]] = field(default_factory=list)
    # internal
    docker_name: str = ""
    log_config: dict[str, Any] | None = None
    log_lines_sent: int = 0


@dataclass
class TrackedTask:
    account_id: str
    region: str
    cluster_name: str
    task: Any  # moto.ecs.models.Task
    containers: list[ContainerRecord]
    # (target group ARN, IP, port) registered for this task
    lb_targets: list[tuple[str, str, int]] = field(default_factory=list)
    running_since: float | None = None


class TaskRunner:
    """Starts, watches and stops the containers of ECS tasks."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tasks: dict[str, TrackedTask] = {}
        # tasks whose containers are being stopped in the background
        self._stopping: dict[str, TrackedTask] = {}
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ecs-task")
        self._loop_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._docker_available: bool | None = None
        # service ARN -> (failed starts in a row, time of the next start attempt)
        self._service_backoff: dict[str, tuple[int, float]] = {}

    # ------------------------------------------------------------------ setup

    @property
    def enabled(self) -> bool:
        if not config.ECS_RUN_CONTAINERS:
            return False
        if self._docker_available is None:
            try:
                self._docker_available = DOCKER_CLIENT.has_docker()
            except Exception:
                self._docker_available = False
            if not self._docker_available:
                LOG.warning("Docker is not available: ECS tasks are recorded but no containers run")
        return self._docker_available

    def ensure_started(self) -> None:
        """Start the monitor loop, which also starts the tasks of services."""
        if self.enabled:
            self._ensure_loop()

    def _ensure_loop(self) -> None:
        with self._lock:
            if self._loop_thread and self._loop_thread.is_alive():
                return
            self._stop_event.clear()
            self._loop_thread = threading.Thread(
                target=self._run_loop, name="ecs-task-monitor", daemon=True
            )
            self._loop_thread.start()

    def shutdown(self) -> None:
        """Stop the monitor loop and remove all containers (service stop or state reset)."""
        self._stop_event.set()
        with self._lock:
            tracked = list(self._tasks.values()) + list(self._stopping.values())
            self._tasks.clear()
            self._stopping.clear()
        for item in tracked:
            for record in item.containers:
                self._remove_container(record)

    # ------------------------------------------------------------ public API

    def launch(self, backend: Any, task: Any) -> None:
        """Start the containers of a task that Moto has just created."""
        if not self.enabled:
            return
        # stop Moto from moving the status on its own; this runner sets it
        task._transitions = []
        task.last_status = "PROVISIONING"
        task.desired_status = "RUNNING"
        task.created_at = getattr(task, "created_at", None) or _now()

        task_definition = backend.describe_task_definition(task.task_definition_arn)
        overrides = {o.get("name"): o for o in (task.overrides or {}).get("containerOverrides", [])}
        records = []
        for definition in task_definition.container_definitions:
            name = definition.get("name")
            records.append(
                ContainerRecord(
                    container_arn=f"arn:aws:ecs:{backend.region_name}:{backend.account_id}:container/{task.cluster_name}/{task.id}/{name}",
                    task_arn=task.task_arn,
                    name=name,
                    image=definition.get("image"),
                    essential=definition.get("essential", True),
                    cpu=str(definition["cpu"]) if definition.get("cpu") is not None else None,
                    memory=str(definition["memory"])
                    if definition.get("memory") is not None
                    else None,
                    docker_name=_container_name(task.cluster_name, task.id, name),
                    log_config=definition.get("logConfiguration"),
                )
            )
        task.containers = records
        tracked = TrackedTask(
            account_id=backend.account_id,
            region=backend.region_name,
            cluster_name=task.cluster_name,
            task=task,
            containers=records,
        )
        with self._lock:
            self._tasks[task.task_arn] = tracked
        self._ensure_loop()
        self._executor.submit(self._start_task, tracked, task_definition, overrides)

    def stop(self, task_arn: str, reason: str, stop_code: str = "UserInitiated") -> None:
        """Stop the containers of a task in the background, as AWS does.

        The task shows ``desiredStatus=STOPPED`` at once and ``lastStatus=STOPPED``
        when its containers have stopped. Unknown tasks are ignored.
        """
        with self._lock:
            tracked = self._tasks.pop(task_arn, None)
            if tracked:
                self._stopping[task_arn] = tracked
        if not tracked:
            return
        # the load balancer stops sending requests before the containers stop
        self._deregister_targets(tracked)
        task = tracked.task
        task._transitions = []
        task.desired_status = "STOPPED"
        task.stopped_reason = reason
        task.stop_code = stop_code
        task.stopping_at = _now()
        # Moto's StopTask has already set STOPPED; the containers are still running
        task.last_status = "DEACTIVATING"
        self._executor.submit(self._stop_tracked, tracked, reason, stop_code)

    def running_tasks(self, account_id: str, region: str) -> list[dict[str, Any]]:
        """RUNNING tasks with their task definition and container IDs (for metrics)."""
        from moto.ecs.models import ecs_backends

        with self._lock:
            tracked = [
                t
                for t in self._tasks.values()
                if t.account_id == account_id
                and t.region == region
                and t.task.last_status == "RUNNING"
            ]
        result = []
        for item in tracked:
            try:
                task_definition = ecs_backends[account_id][region].describe_task_definition(
                    item.task.task_definition_arn
                )
            except Exception:
                continue
            result.append(
                {
                    "task": item.task,
                    "task_definition": task_definition,
                    "container_ids": [r.runtime_id for r in item.containers if r.runtime_id],
                }
            )
        return result

    # ------------------------------------------------------- load balancers

    def _service_of(self, tracked: TrackedTask) -> Any | None:
        from moto.ecs.models import ecs_backends

        group = getattr(tracked.task, "group", "") or ""
        if not group.startswith(SERVICE_GROUP_PREFIX):
            return None
        backend = ecs_backends[tracked.account_id][tracked.region]
        return backend.services.get(f"{tracked.cluster_name}:{group[len(SERVICE_GROUP_PREFIX) :]}")

    def _register_targets(self, tracked: TrackedTask) -> None:
        """Register the task with the target groups of its service (``loadBalancers``)."""
        service = self._service_of(tracked)
        if service is None or not getattr(service, "load_balancers", None):
            return
        elbv2 = connect_to(aws_access_key_id=tracked.account_id, region_name=tracked.region).elbv2
        for lb in service.load_balancers:
            target_group_arn = lb.get("targetGroupArn")
            record = next(
                (r for r in tracked.containers if r.name == lb.get("containerName")), None
            )
            if not target_group_arn or record is None or not record.network_interfaces:
                continue
            ip = record.network_interfaces[0]["privateIpv4Address"]
            port = int(lb.get("containerPort") or 0)
            try:
                elbv2.register_targets(
                    TargetGroupArn=target_group_arn, Targets=[{"Id": ip, "Port": port}]
                )
                tracked.lb_targets.append((target_group_arn, ip, port))
            except Exception as e:
                LOG.warning(
                    "Cannot register task %s in %s: %s", tracked.task.task_arn, target_group_arn, e
                )

    def _deregister_targets(self, tracked: TrackedTask) -> None:
        if not tracked.lb_targets:
            return
        elbv2 = connect_to(aws_access_key_id=tracked.account_id, region_name=tracked.region).elbv2
        for target_group_arn, ip, port in tracked.lb_targets:
            try:
                elbv2.deregister_targets(
                    TargetGroupArn=target_group_arn, Targets=[{"Id": ip, "Port": port}]
                )
            except Exception as e:
                LOG.debug("Cannot deregister %s:%s from %s: %s", ip, port, target_group_arn, e)
        tracked.lb_targets = []

    def stop_unhealthy_target(
        self, account_id: str, region: str, target_group_arn: str, ip: str
    ) -> None:
        """Replace the service task behind a target that fails health checks, as ECS does.

        The service's ``healthCheckGracePeriodSeconds`` is respected.
        """
        with self._lock:
            match = next(
                (
                    t
                    for t in self._tasks.values()
                    if t.account_id == account_id
                    and t.region == region
                    and any(tg == target_group_arn and i == ip for tg, i, _ in t.lb_targets)
                ),
                None,
            )
        if match is None:
            return
        service = self._service_of(match)
        grace = float(getattr(service, "_mocksy_health_check_grace_period", 0) or 0)
        if match.running_since and time.monotonic() - match.running_since < grace:
            return
        name = target_group_arn.split(":", 5)[-1]
        self.stop(
            match.task.task_arn,
            f"Task failed ELB health checks in (target-group {target_group_arn})",
            "ServiceSchedulerInitiated",
        )
        LOG.info(
            "Replacing ECS task %s: it failed the health checks of %s", match.task.task_arn, name
        )

    # -------------------------------------------------------------- starting

    def _start_task(
        self, tracked: TrackedTask, task_definition: Any, overrides: dict[str, dict]
    ) -> None:
        task = tracked.task
        try:
            task.last_status = "PENDING"
            task.pull_started_at = _now()
            for record in tracked.containers:
                self._pull_image(record.image)
            task.pull_stopped_at = _now()

            definitions = {d.get("name"): d for d in task_definition.container_definitions}
            for record in tracked.containers:
                if task.desired_status == "STOPPED":
                    # StopTask arrived while the task was starting
                    return
                self._start_container(
                    tracked, record, definitions[record.name], overrides.get(record.name, {})
                )
            task.last_status = "RUNNING"
            task.started_at = _now()
            task.connectivity = "CONNECTED"
            task.connectivity_at = task.started_at
            self._update_task_ip(tracked)
            tracked.running_since = time.monotonic()
            self._register_targets(tracked)
        except TaskStartError as e:
            LOG.warning("ECS task %s cannot start: %s", task.task_arn, e)
            self.stop(task.task_arn, str(e), e.stop_code)
        except Exception as e:
            LOG.exception("ECS task %s cannot start", task.task_arn)
            self.stop(task.task_arn, f"TaskFailedToStart: {e}", "TaskFailedToStart")

    def _pull_image(self, image: str) -> None:
        try:
            DOCKER_CLIENT.inspect_image(image, pull=False)
            return
        except Exception:
            pass
        try:
            DOCKER_CLIENT.pull_image(image)
        except Exception as e:
            raise TaskStartError(
                f"CannotPullContainerError: pull image manifest has been retried: {image}: {e}"
            ) from e

    def _start_container(
        self,
        tracked: TrackedTask,
        record: ContainerRecord,
        definition: dict[str, Any],
        override: dict[str, Any],
    ) -> None:
        env = self._environment(tracked, definition, override)
        network = config.ECS_DOCKER_NETWORK or get_main_container_network()
        command = override.get("command") or definition.get("command")
        mem_limit = None
        if definition.get("memory"):
            mem_limit = f"{int(definition['memory'])}m"

        self._create_log_stream(tracked, record)
        # a container with the same name can remain from a crash; replace it
        DOCKER_CLIENT.remove_container(record.docker_name, force=True, check_existence=True)
        container_id = DOCKER_CLIENT.create_container(
            record.image,
            name=record.docker_name,
            entrypoint=definition.get("entryPoint"),
            command=command,
            env_vars=env,
            network=network,
            workdir=definition.get("workingDirectory"),
            user=definition.get("user"),
            labels={
                LABEL_MANAGED: "true",
                LABEL_TASK_ARN: tracked.task.task_arn,
                LABEL_CONTAINER: record.name,
            },
            mem_limit=mem_limit,
        )
        DOCKER_CLIENT.start_container(container_id)
        record.runtime_id = container_id
        record.last_status = "RUNNING"
        try:
            ip = DOCKER_CLIENT.get_container_ipv4_for_network(container_id, network)
            record.network_interfaces = [
                {"attachmentId": tracked.task.id, "privateIpv4Address": ip}
            ]
        except Exception as e:
            LOG.debug("Cannot read IP of container %s: %s", record.docker_name, e)

    def _environment(
        self, tracked: TrackedTask, definition: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, str]:
        env: dict[str, str] = {
            "AWS_REGION": tracked.region,
            "AWS_DEFAULT_REGION": tracked.region,
            "AWS_ACCESS_KEY_ID": tracked.account_id,
            "AWS_SECRET_ACCESS_KEY": "test",
        }
        if not config.ECS_DISABLE_AWS_ENDPOINT_URL:
            network = config.ECS_DOCKER_NETWORK or get_main_container_network()
            host = get_endpoint_for_network(network)
            env["AWS_ENDPOINT_URL"] = f"http://{host}:{config.GATEWAY_LISTEN[0].port}"

        for item in definition.get("environment") or []:
            env[item["name"]] = item.get("value", "")
        for item in override.get("environment") or []:
            env[item["name"]] = item.get("value", "")
        for item in definition.get("secrets") or []:
            env[item["name"]] = self._resolve_secret(tracked, item["valueFrom"])
        return env

    def _resolve_secret(self, tracked: TrackedTask, value_from: str) -> str:
        """Return the value of a ``secrets`` entry.

        ``valueFrom`` is a Secrets Manager ARN, optionally with ``:json-key:version-stage:version-id``,
        or an SSM parameter name or ARN.
        """
        clients = connect_to(aws_access_key_id=tracked.account_id, region_name=tracked.region)
        try:
            if ":secretsmanager:" in value_from:
                parts = value_from.split(":")
                # arn:aws:secretsmanager:region:account:secret:name-suffix[:json-key:stage:version]
                secret_id = ":".join(parts[:7])
                json_key = parts[7] if len(parts) > 7 and parts[7] else None
                stage = parts[8] if len(parts) > 8 and parts[8] else None
                version = parts[9] if len(parts) > 9 and parts[9] else None
                kwargs: dict[str, str] = {"SecretId": secret_id}
                if stage:
                    kwargs["VersionStage"] = stage
                if version:
                    kwargs["VersionId"] = version
                value = clients.secretsmanager.get_secret_value(**kwargs)["SecretString"]
                if json_key:
                    value = json.loads(value)[json_key]
                    value = value if isinstance(value, str) else json.dumps(value)
                return value
            name = value_from
            if ":ssm:" in value_from:
                # arn:aws:ssm:region:account:parameter/name -> /name
                name = value_from.split(":parameter", 1)[1]
            return clients.ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]
        except Exception as e:
            raise TaskStartError(
                f"ResourceInitializationError: unable to pull secrets or registry auth: "
                f"retrieve secret from {value_from}: {e}"
            ) from e

    # ----------------------------------------------------------------- logs

    def _log_target(self, record: ContainerRecord, task_id: str) -> tuple[str, str] | None:
        log_config = record.log_config or {}
        if log_config.get("logDriver") != "awslogs":
            return None
        options = log_config.get("options") or {}
        group = options.get("awslogs-group")
        if not group:
            return None
        prefix = options.get("awslogs-stream-prefix")
        stream = f"{prefix}/{record.name}/{task_id}" if prefix else task_id
        return group, stream

    def _create_log_stream(self, tracked: TrackedTask, record: ContainerRecord) -> None:
        target = self._log_target(record, tracked.task.id)
        if not target:
            return
        group, stream = target
        options = (record.log_config or {}).get("options") or {}
        logs = connect_to(aws_access_key_id=tracked.account_id, region_name=tracked.region).logs
        if str(options.get("awslogs-create-group", "")).lower() == "true":
            try:
                logs.create_log_group(logGroupName=group)
            except logs.exceptions.ResourceAlreadyExistsException:
                pass
        try:
            logs.create_log_stream(logGroupName=group, logStreamName=stream)
        except logs.exceptions.ResourceAlreadyExistsException:
            pass
        except logs.exceptions.ResourceNotFoundException as e:
            # AWS fails the task in the same way when the log group is missing
            raise TaskStartError(
                f"ResourceInitializationError: failed to validate logger args: "
                f"The specified log group does not exist: {group}"
            ) from e

    def _ship_logs(self, tracked: TrackedTask, record: ContainerRecord) -> None:
        target = self._log_target(record, tracked.task.id)
        if not target or not record.runtime_id:
            return
        try:
            output = DOCKER_CLIENT.get_container_logs(record.runtime_id, safe=True)
        except Exception:
            return
        lines = output.splitlines()
        new_lines = lines[record.log_lines_sent :]
        if not new_lines:
            return
        group, stream = target
        timestamp = int(_now().timestamp() * 1000)
        events = [{"timestamp": timestamp, "message": line} for line in new_lines if line]
        try:
            if events:
                connect_to(
                    aws_access_key_id=tracked.account_id, region_name=tracked.region
                ).logs.put_log_events(logGroupName=group, logStreamName=stream, logEvents=events)
            record.log_lines_sent = len(lines)
        except Exception as e:
            LOG.debug("Cannot send logs of %s: %s", record.docker_name, e)

    # -------------------------------------------------------------- stopping

    def _stop_tracked(self, tracked: TrackedTask, reason: str, stop_code: str) -> None:
        task = tracked.task
        task.last_status = "STOPPING"
        for record in tracked.containers:
            if record.runtime_id and record.last_status == "RUNNING":
                try:
                    DOCKER_CLIENT.stop_container(record.runtime_id, timeout=10)
                except Exception as e:
                    LOG.debug("Cannot stop container %s: %s", record.docker_name, e)
            self._read_exit_code(record)
            self._ship_logs(tracked, record)
            record.last_status = "STOPPED"
            self._remove_container(record)
        task.last_status = "STOPPED"
        task.stopped_reason = reason
        task.stop_code = stop_code
        task.stopped_at = _now()
        task.execution_stopped_at = task.stopped_at
        with self._lock:
            self._stopping.pop(task.task_arn, None)

    def _read_exit_code(self, record: ContainerRecord) -> None:
        if not record.runtime_id or record.exit_code is not None:
            return
        try:
            state = DOCKER_CLIENT.inspect_container(record.runtime_id).get("State", {})
            if not state.get("Running"):
                record.exit_code = state.get("ExitCode")
        except Exception:
            pass

    def _remove_container(self, record: ContainerRecord) -> None:
        if not record.runtime_id or not config.ECS_REMOVE_CONTAINERS:
            return
        try:
            DOCKER_CLIENT.remove_container(record.runtime_id, force=True)
        except Exception as e:
            LOG.debug("Cannot remove container %s: %s", record.docker_name, e)

    def _update_task_ip(self, tracked: TrackedTask) -> None:
        """Show the IP of the first container in the task's network interface attachment."""
        ip = next(
            (
                r.network_interfaces[0]["privateIpv4Address"]
                for r in tracked.containers
                if r.network_interfaces
            ),
            None,
        )
        if not ip:
            return
        for attachment in getattr(tracked.task, "attachments", []) or []:
            for detail in attachment.get("details", []):
                if detail.get("name") == "privateIPv4Address":
                    detail["value"] = ip

    # ------------------------------------------------------------ the loop

    def _run_loop(self) -> None:
        while not self._stop_event.wait(config.ECS_MONITOR_INTERVAL):
            try:
                self.check_containers()
                self.reconcile_services()
            except Exception:
                LOG.exception("Error in the ECS task monitor")

    def check_containers(self) -> None:
        """Send new log lines; stop tasks whose essential container has exited."""
        with self._lock:
            tracked_tasks = list(self._tasks.values())
        for tracked in tracked_tasks:
            if tracked.task.last_status != "RUNNING":
                continue
            exited_essential: ContainerRecord | None = None
            for record in tracked.containers:
                self._ship_logs(tracked, record)
                if record.last_status != "RUNNING" or not record.runtime_id:
                    continue
                try:
                    state = DOCKER_CLIENT.inspect_container(record.runtime_id).get("State", {})
                except Exception:
                    state = {"Running": False, "ExitCode": None}
                if not state.get("Running"):
                    record.last_status = "STOPPED"
                    record.exit_code = state.get("ExitCode")
                    if record.essential and not exited_essential:
                        exited_essential = record
            if exited_essential:
                self.stop(
                    tracked.task.task_arn,
                    "Essential container in task exited",
                    "EssentialContainerExited",
                )

    def reconcile_services(self) -> None:
        """Keep the running task count of each ACTIVE service equal to desiredCount."""
        from moto.ecs.models import ecs_backends

        for account_id, regions in list(ecs_backends.items()):
            for region, backend in list(regions.items()):
                for service in list(backend.services.values()):
                    try:
                        self._reconcile_service(backend, service)
                    except Exception:
                        LOG.exception("Cannot reconcile ECS service %s", service.arn)

    def _service_tasks(self, backend: Any, service: Any) -> list[Any]:
        group = f"{SERVICE_GROUP_PREFIX}{service.name}"
        tasks = backend.tasks.get(service.cluster_name, {}).values()
        return [
            t for t in tasks if getattr(t, "group", None) == group and t.desired_status == "RUNNING"
        ]

    def _reconcile_service(self, backend: Any, service: Any) -> None:
        active = self._service_tasks(backend, service)
        desired = service.desired_count if service.status == "ACTIVE" else 0
        task_definition = service.task_definition

        # tasks of an older task definition are replaced (rolling update, one step)
        outdated = [t for t in active if t.task_definition_arn != task_definition]
        for task in outdated:
            self.stop(
                task.task_arn, "Task stopped by a new deployment", "ServiceSchedulerInitiated"
            )
            active.remove(task)

        if len(active) > desired:
            for task in active[desired:]:
                self.stop(
                    task.task_arn,
                    "Scaling activity initiated by (deployment ecs-svc)",
                    "ServiceSchedulerInitiated",
                )
            active = active[:desired]
        elif len(active) < desired and self._may_start(backend, service):
            missing = desired - len(active)
            deployment_id = (service.deployments or [{}])[0].get("id", "ecs-svc")
            new_tasks = backend.run_task(
                service.cluster_name,
                task_definition,
                missing,
                None,
                deployment_id,
                None,
                service.launch_type or "FARGATE",
                networking_configuration=service.network_configuration or None,
                group=f"{SERVICE_GROUP_PREFIX}{service.name}",
                platform_version=getattr(service, "platform_version", None),
            )
            active.extend(new_tasks)

        running = sum(1 for t in active if t.last_status == "RUNNING")
        service.running_count = running
        service.pending_count = len(active) - running

    def _may_start(self, backend: Any, service: Any) -> bool:
        """Back off when the service's tasks keep failing to start, as AWS does.

        After each start failure the wait doubles: 5 s, 10 s, 20 s, ... up to 5 minutes.
        A task that reaches RUNNING resets the wait.
        """
        group = f"{SERVICE_GROUP_PREFIX}{service.name}"
        tasks = [
            t
            for t in backend.tasks.get(service.cluster_name, {}).values()
            if getattr(t, "group", None) == group
        ]
        if any(t.last_status == "RUNNING" for t in tasks):
            self._service_backoff.pop(service.arn, None)
            return True

        failures, next_attempt = self._service_backoff.get(service.arn, (0, 0.0))
        for task in tasks:
            if getattr(task, "stop_code", None) != "TaskFailedToStart":
                continue
            if getattr(task, "_mocksy_backoff_counted", False):
                continue
            task._mocksy_backoff_counted = True
            failures += 1
            delay = min(5 * 2 ** (failures - 1), 300)
            next_attempt = time.monotonic() + delay
            LOG.warning(
                "Tasks of ECS service %s fail to start (%s); next try in %ds",
                service.arn,
                task.stopped_reason,
                delay,
            )
        self._service_backoff[service.arn] = (failures, next_attempt)
        return time.monotonic() >= next_attempt


TASK_RUNNER = TaskRunner()
