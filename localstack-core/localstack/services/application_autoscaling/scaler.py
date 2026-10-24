"""Applies Application Auto Scaling policies to ECS services (issue #5, phase 2).

Moto stores scalable targets and scaling policies. This module acts on them.
Every ``APPLICATION_AUTOSCALING_INTERVAL`` seconds:

1. For each ECS service with running task containers, mocksy publishes
   ``AWS/ECS`` ``CPUUtilization`` and ``MemoryUtilization`` (dimensions
   ``ClusterName``, ``ServiceName``) to CloudWatch, measured with ``docker stats``
   against the task's ``cpu`` and ``memory``, as AWS does.
2. Each ECS scalable target (``ecs:service:DesiredCount``) is evaluated:
   - **Target tracking:** the metric (predefined ``ECSServiceAverageCPUUtilization``
     or ``ECSServiceAverageMemoryUtilization``, or a customized CloudWatch metric
     such as a queue depth) is read from CloudWatch. The new capacity is
     ``ceil(current * value / target)``. Scale-in is skipped with ``DisableScaleIn``.
   - **Step scaling:** a policy acts when a CloudWatch alarm that names it in
     ``AlarmActions`` is in ``ALARM``. The step is chosen by
     ``metric value - alarm threshold``.
   - The result stays within ``MinCapacity`` and ``MaxCapacity``, waits for the
     cooldowns, and is applied with ``UpdateService``. Each change is a scaling
     activity (DescribeScalingActivities).

Suspended targets (``SuspendedState``) are not scaled. Only the ``ecs``
namespace is acted on; other namespaces are recorded only.
"""

from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from localstack import config
from localstack.aws.connect import connect_to

LOG = logging.getLogger(__name__)

ECS_DIMENSION = "ecs:service:DesiredCount"
DEFAULT_COOLDOWN = 300
PREDEFINED_ECS_METRICS = {
    "ECSServiceAverageCPUUtilization": "CPUUtilization",
    "ECSServiceAverageMemoryUtilization": "MemoryUtilization",
}


def _now() -> datetime:
    return datetime.now(tz=UTC)


class Scaler:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        # (account, region) -> activities, newest first
        self._activities: dict[tuple[str, str], list[dict[str, Any]]] = {}
        # policy ARN -> time.monotonic() of its last change, for cooldowns
        self._last_change: dict[str, tuple[float, str]] = {}
        self._warned: set[str] = set()

    # ---------------------------------------------------------------- loop

    def ensure_started(self) -> None:
        if not config.APPLICATION_AUTOSCALING_RUN:
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="app-autoscaling", daemon=True)
            self._thread.start()

    def shutdown(self) -> None:
        self._stop.set()
        with self._lock:
            self._activities.clear()
            self._last_change.clear()

    def _run(self) -> None:
        while not self._stop.wait(config.APPLICATION_AUTOSCALING_INTERVAL):
            try:
                self.evaluate_once()
            except Exception:
                LOG.exception("Error while evaluating scaling policies")

    def evaluate_once(self) -> None:
        from moto.applicationautoscaling.models import applicationautoscaling_backends

        for account_id, regions in list(applicationautoscaling_backends.items()):
            for region, backend in list(regions.items()):
                if not backend.targets:
                    continue
                self._publish_ecs_metrics(account_id, region)
                for target in list(backend.targets.get(ECS_DIMENSION, {}).values()):
                    if target.service_namespace != "ecs":
                        continue
                    try:
                        self._evaluate_target(account_id, region, backend, target)
                    except Exception:
                        LOG.exception("Cannot evaluate scaling for %s", target.resource_id)

    # ----------------------------------------------------------- ECS metrics

    def _publish_ecs_metrics(self, account_id: str, region: str) -> None:
        """Publish CPU and memory utilization of ECS services, as AWS does every minute."""
        from localstack.services.ecs.task_runner import TASK_RUNNER
        from localstack.utils.docker_utils import DOCKER_CLIENT

        per_service: dict[tuple[str, str], list[tuple[float, float]]] = {}
        for item in TASK_RUNNER.running_tasks(account_id, region):
            task, task_definition = item["task"], item["task_definition"]
            group = getattr(task, "group", "") or ""
            if not group.startswith("service:"):
                continue
            task_cpu = float(task_definition.cpu or 0) or 1024.0
            task_memory = float(task_definition.memory or 0) or 0.0
            cpu = memory = 0.0
            for runtime_id in item["container_ids"]:
                try:
                    stats = DOCKER_CLIENT.get_container_stats(runtime_id)
                except Exception:
                    continue
                cpu += float(stats.get("CPUPerc") or 0)
                memory += float((stats.get("MemUsage") or (0, 0))[0] or 0)
            # CPUPerc is percent of one core; a task reserves task_cpu / 1024 cores
            cpu_utilization = cpu * 1024.0 / task_cpu
            memory_utilization = (
                memory / (task_memory * 1024 * 1024) * 100.0 if task_memory else 0.0
            )
            key = (task.cluster_name, group.split(":", 1)[1])
            per_service.setdefault(key, []).append((cpu_utilization, memory_utilization))

        if not per_service:
            return
        cloudwatch = connect_to(aws_access_key_id=account_id, region_name=region).cloudwatch
        data = []
        for (cluster, service), values in per_service.items():
            dimensions = [
                {"Name": "ClusterName", "Value": cluster},
                {"Name": "ServiceName", "Value": service},
            ]
            for name, index in (("CPUUtilization", 0), ("MemoryUtilization", 1)):
                data.append(
                    {
                        "MetricName": name,
                        "Dimensions": dimensions,
                        "Value": sum(v[index] for v in values) / len(values),
                        "Unit": "Percent",
                    }
                )
        for start in range(0, len(data), 20):
            cloudwatch.put_metric_data(Namespace="AWS/ECS", MetricData=data[start : start + 20])

    # ------------------------------------------------------------ evaluation

    def _evaluate_target(self, account_id: str, region: str, backend: Any, target: Any) -> None:
        suspended = target.suspended_state or {}
        if suspended.get("DynamicScalingInSuspended") and suspended.get(
            "DynamicScalingOutSuspended"
        ):
            return
        _, cluster, service_name = target.resource_id.split("/", 2)
        clients = connect_to(aws_access_key_id=account_id, region_name=region)
        services = clients.ecs.describe_services(cluster=cluster, services=[service_name])
        if not services["services"] or services["services"][0]["status"] != "ACTIVE":
            return
        current = services["services"][0]["desiredCount"]

        policies = [
            p
            for p in backend.policies.values()
            if p.resource_id == target.resource_id and p.scalable_dimension == ECS_DIMENSION
        ]
        for policy in policies:
            if policy.policy_type == "TargetTrackingScaling":
                desired, reason = self._target_tracking(
                    clients, policy, cluster, service_name, current
                )
                cooldowns = policy.target_tracking_scaling_policy_configuration or {}
                scale_out_cooldown = cooldowns.get("ScaleOutCooldown", DEFAULT_COOLDOWN)
                scale_in_cooldown = cooldowns.get("ScaleInCooldown", DEFAULT_COOLDOWN)
            elif policy.policy_type == "StepScaling":
                desired, reason = self._step_scaling(clients, policy, current)
                step = policy.step_scaling_policy_configuration or {}
                scale_out_cooldown = scale_in_cooldown = step.get("Cooldown", DEFAULT_COOLDOWN)
            else:
                continue
            if desired is None:
                continue

            desired = self._clamp(target, desired)
            if desired == current:
                continue
            scaling_out = desired > current
            if scaling_out and suspended.get("DynamicScalingOutSuspended"):
                continue
            if not scaling_out and suspended.get("DynamicScalingInSuspended"):
                continue
            if self._in_cooldown(
                policy.policy_arn, scaling_out, scale_out_cooldown, scale_in_cooldown
            ):
                continue

            clients.ecs.update_service(cluster=cluster, service=service_name, desiredCount=desired)
            self._last_change[policy.policy_arn] = (
                time.monotonic(),
                "out" if scaling_out else "in",
            )
            self._record(account_id, region, target, policy, current, desired, reason)
            LOG.info("Scaled %s from %s to %s (%s)", target.resource_id, current, desired, reason)
            # one change per target and evaluation, like a single scaling activity in AWS
            return

    @staticmethod
    def _clamp(target: Any, desired: int) -> int:
        if target.min_capacity is not None:
            desired = max(desired, int(target.min_capacity))
        if target.max_capacity is not None:
            desired = min(desired, int(target.max_capacity))
        return max(desired, 0)

    def _in_cooldown(
        self, policy_arn: str, scaling_out: bool, out_cooldown: float, in_cooldown: float
    ) -> bool:
        last = self._last_change.get(policy_arn)
        if not last:
            return False
        changed_at, _ = last
        cooldown = out_cooldown if scaling_out else in_cooldown
        return time.monotonic() - changed_at < float(cooldown or 0)

    # ------------------------------------------------------- target tracking

    def _target_tracking(
        self, clients: Any, policy: Any, cluster: str, service: str, current: int
    ) -> tuple[int | None, str]:
        configuration = policy.target_tracking_scaling_policy_configuration or {}
        target_value = float(configuration.get("TargetValue") or 0)
        if target_value <= 0:
            return None, ""

        predefined = configuration.get("PredefinedMetricSpecification")
        customized = configuration.get("CustomizedMetricSpecification")
        if predefined and predefined.get("PredefinedMetricType") == "ALBRequestCountPerTarget":
            # ResourceLabel: app/<lb-name>/<lb-id>/targetgroup/<tg-name>/<tg-id>
            label = predefined.get("ResourceLabel") or ""
            target_group = label[label.find("targetgroup/") :] if "targetgroup/" in label else ""
            if not target_group:
                self._warn_once(
                    f"{policy.policy_arn}:label",
                    "Policy %s: ALBRequestCountPerTarget needs a ResourceLabel",
                    policy.policy_name,
                )
                return None, ""
            value = self._latest(
                clients,
                "AWS/ApplicationELB",
                "RequestCountPerTarget",
                [{"Name": "TargetGroup", "Value": target_group}],
                "Sum",
            )
            if value is None:
                # no requests in the period: AWS reports no datapoint, scale in toward 0 requests
                value = 0.0
            label = "ALBRequestCountPerTarget"
        elif predefined:
            metric_type = predefined.get("PredefinedMetricType")
            metric_name = PREDEFINED_ECS_METRICS.get(metric_type)
            if not metric_name:
                self._warn_once(
                    f"{policy.policy_arn}:{metric_type}",
                    "Predefined metric %s is not supported by mocksy (policy %s)",
                    metric_type,
                    policy.policy_name,
                )
                return None, ""
            value = self._latest(
                clients,
                "AWS/ECS",
                metric_name,
                [
                    {"Name": "ClusterName", "Value": cluster},
                    {"Name": "ServiceName", "Value": service},
                ],
                "Average",
            )
            label = metric_type
        elif customized:
            if customized.get("Metrics"):
                self._warn_once(
                    policy.policy_arn,
                    "Metric math in policy %s is not supported by mocksy",
                    policy.policy_name,
                )
                return None, ""
            value = self._latest(
                clients,
                customized.get("Namespace"),
                customized.get("MetricName"),
                customized.get("Dimensions") or [],
                customized.get("Statistic") or "Average",
            )
            label = f"{customized.get('Namespace')}/{customized.get('MetricName')}"
        else:
            return None, ""

        if value is None:
            return None, ""
        if current == 0:
            desired = 1 if value > target_value else 0
        else:
            desired = math.ceil(current * value / target_value)
        if desired < current and configuration.get("DisableScaleIn"):
            return None, ""
        reason = f"{label} is {value:.2f}, target {target_value:g}"
        return desired, reason

    @staticmethod
    def _latest(
        clients: Any,
        namespace: str | None,
        metric_name: str | None,
        dimensions: list[dict[str, str]],
        statistic: str,
    ) -> float | None:
        """Latest datapoint of the metric over the last minutes, or None without data."""
        if not namespace or not metric_name:
            return None
        end = _now()
        period = max(int(config.APPLICATION_AUTOSCALING_METRIC_PERIOD), 1)
        result = clients.cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=end - timedelta(seconds=period * 3),
            EndTime=end + timedelta(seconds=1),
            Period=period,
            Statistics=[statistic],
        )
        points = sorted(result.get("Datapoints") or [], key=lambda p: p["Timestamp"])
        if not points:
            return None
        return float(points[-1][statistic])

    # ---------------------------------------------------------- step scaling

    def _step_scaling(self, clients: Any, policy: Any, current: int) -> tuple[int | None, str]:
        configuration = policy.step_scaling_policy_configuration or {}
        alarms = self._alarms_for(clients, policy.policy_arn)
        alarm = next((a for a in alarms if a.get("StateValue") == "ALARM"), None)
        if not alarm:
            return None, ""
        value = self._latest(
            clients,
            alarm.get("Namespace"),
            alarm.get("MetricName"),
            alarm.get("Dimensions") or [],
            alarm.get("Statistic") or "Average",
        )
        if value is None:
            return None, ""
        difference = value - float(alarm.get("Threshold") or 0)
        adjustment = None
        for step in configuration.get("StepAdjustments") or []:
            lower = step.get("MetricIntervalLowerBound")
            upper = step.get("MetricIntervalUpperBound")
            if (lower is None or difference >= float(lower)) and (
                upper is None or difference < float(upper)
            ):
                adjustment = int(step["ScalingAdjustment"])
                break
        if adjustment is None:
            return None, ""

        adjustment_type = configuration.get("AdjustmentType", "ChangeInCapacity")
        if adjustment_type == "ExactCapacity":
            desired = adjustment
        elif adjustment_type == "PercentChangeInCapacity":
            change = current * adjustment / 100.0
            change = math.ceil(change) if change > 0 else math.floor(change)
            minimum = configuration.get("MinAdjustmentMagnitude")
            if minimum and abs(change) < int(minimum):
                change = int(minimum) if change >= 0 else -int(minimum)
            desired = current + change
        else:
            desired = current + adjustment
        reason = (
            f"alarm {alarm['AlarmName']} is in ALARM ({alarm.get('MetricName')} is {value:.2f})"
        )
        return desired, reason

    @staticmethod
    def _alarms_for(clients: Any, policy_arn: str) -> list[dict[str, Any]]:
        alarms = []
        paginator = clients.cloudwatch.get_paginator("describe_alarms")
        for page in paginator.paginate(AlarmTypes=["MetricAlarm"]):
            for alarm in page.get("MetricAlarms", []):
                if any(action.startswith(policy_arn) for action in alarm.get("AlarmActions", [])):
                    alarms.append(alarm)
        return alarms

    # -------------------------------------------------------------- history

    def _record(
        self,
        account_id: str,
        region: str,
        target: Any,
        policy: Any,
        current: int,
        desired: int,
        reason: str,
    ) -> None:
        now = _now()
        activity = {
            "ActivityId": str(uuid.uuid4()),
            "ServiceNamespace": target.service_namespace,
            "ResourceId": target.resource_id,
            "ScalableDimension": target.scalable_dimension,
            "Description": f"Setting desired count to {desired}.",
            "Cause": (
                f"monitor alarm or metric for policy {policy.policy_name}: {reason}, "
                f"desired count changed from {current} to {desired}"
            ),
            "StartTime": now,
            "EndTime": now,
            "StatusCode": "Successful",
            "StatusMessage": f"Successfully set desired count to {desired}.",
        }
        with self._lock:
            self._activities.setdefault((account_id, region), []).insert(0, activity)

    def activities(
        self, account_id: str, region: str, namespace: str, resource_id: str | None
    ) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._activities.get((account_id, region), []))
        return [
            a
            for a in items
            if a["ServiceNamespace"] == namespace
            and (resource_id is None or a["ResourceId"] == resource_id)
        ]

    def _warn_once(self, key: str, message: str, *args: Any) -> None:
        if key in self._warned:
            return
        self._warned.add(key)
        LOG.warning(message, *args)


SCALER = Scaler()
