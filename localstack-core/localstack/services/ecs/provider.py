"""ECS provider.

Operations are handled by Moto through the MotoFallbackDispatcher. Tasks run as
Docker containers (see ``task_runner``): RunTask and StartTask start them,
StopTask stops them, and services keep ``desiredCount`` tasks running.

Fixes on top of Moto:
- ``awsvpcConfiguration.securityGroups`` is optional in AWS. When it is missing,
  AWS uses the default security group of the subnet's VPC, and the service and
  task still show the network configuration as it was sent. Moto raises an
  internal error instead. The provider uses the default group inside Moto and
  keeps the stored configuration as sent, so OpenTofu/Terraform shows no change
  on the next plan.
- Moto gives a network interface ``private_dns_name`` only when the VPC has DNS
  hostnames turned on (custom VPCs do not by default), but its ECS tasks always
  read it, so no task could start in such a VPC. The attribute now defaults to
  None.
- With Fargate, memory is usually set on the task definition and not on each
  container. Moto adds up container memory to place tasks and fails with
  TypeError when a container has none. The provider counts such containers
  as 0 MiB.
"""

import copy
import logging
from types import SimpleNamespace
from typing import Any

from moto.ec2.models import ec2_backends
from moto.ec2.models.elastic_network_interfaces import NetworkInterface
from moto.ecs.models import EC2ContainerServiceBackend, Service, Task, ecs_backends

from localstack.aws.api import RequestContext, handler
from localstack.aws.api.ecs import EcsApi
from localstack.services.ecs.task_runner import TASK_RUNNER
from localstack.services.moto import call_moto
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch

LOG = logging.getLogger(__name__)

# see the module docstring; an instance value (DNS hostnames on) still takes precedence
NetworkInterface.private_dns_name = None


def _default_security_group_id(account_id: str, region: str, subnet_id: str) -> str | None:
    """Return the ID of the default security group of the VPC that contains the subnet."""
    ec2_backend = ec2_backends[account_id][region]
    try:
        subnet = ec2_backend.get_subnet(subnet_id)
    except Exception:
        # an unknown subnet is reported by Moto's own validation with the AWS error message
        return None
    try:
        group = ec2_backend.get_default_security_group(subnet.vpc_id)
    except Exception as e:
        LOG.debug("Cannot find default security group for VPC %s: %s", subnet.vpc_id, e)
        return None
    return group.id if group else None


def _with_default_security_group(
    network_configuration: dict[str, Any] | None, account_id: str, region: str
) -> dict[str, Any] | None:
    """Return a copy of the configuration with the default security group added.

    Returns None when the configuration does not need a change.
    """
    if not network_configuration:
        return None
    awsvpc = network_configuration.get("awsvpcConfiguration")
    if not awsvpc or awsvpc.get("securityGroups"):
        return None
    subnets = awsvpc.get("subnets") or []
    if not subnets:
        # Moto reports "subnets can not be empty." with the AWS error
        return None
    group_id = _default_security_group_id(account_id, region, subnets[0])
    if not group_id:
        return None
    filled = copy.deepcopy(network_configuration)
    filled["awsvpcConfiguration"]["securityGroups"] = [group_id]
    return filled


@patch(Service._validate_network)
def _validate_network(fn, self: Service, nc: dict[str, Any]) -> dict[str, Any]:
    filled = _with_default_security_group(nc, self._account_id, self.region_name)
    if filled is None:
        return fn(self, nc)
    fn(self, filled)
    # keep the configuration as sent
    return nc


@patch(Task.__init__)
def _task_init(fn, self: Task, *args, **kwargs):
    original = kwargs.get("networking_configuration")
    # Moto passes the cluster as a keyword or as the first positional argument
    cluster = kwargs.get("cluster", args[0] if args else None)
    backend = kwargs.get("backend")
    filled = None
    if cluster is not None and backend is not None:
        filled = _with_default_security_group(original, backend.account_id, cluster.region_name)
    if filled is None:
        return fn(self, *args, **kwargs)
    kwargs["networking_configuration"] = filled
    fn(self, *args, **kwargs)
    # the network interface uses the default group; the task shows the configuration as sent
    self.network_configuration = original


_MEMORY_KEYS = ("memory", "memoryReservation", "Memory", "MemoryReservation")
_original_calculate_requirements = EC2ContainerServiceBackend._calculate_task_resource_requirements


def _calculate_task_resource_requirements(task_definition) -> dict[str, Any]:
    definitions = task_definition.container_definitions or []
    if all(any(d.get(key) is not None for key in _MEMORY_KEYS) for d in definitions):
        return _original_calculate_requirements(task_definition)
    # Moto reads only container_definitions, so a lightweight stand-in is enough
    filled = [
        d if any(d.get(key) is not None for key in _MEMORY_KEYS) else {**d, "memory": 0}
        for d in definitions
    ]
    return _original_calculate_requirements(SimpleNamespace(container_definitions=filled))


# Moto defines this as a staticmethod, so it is replaced directly
EC2ContainerServiceBackend._calculate_task_resource_requirements = staticmethod(
    _calculate_task_resource_requirements
)


@patch(EC2ContainerServiceBackend.run_task)
def _run_task(fn, self: EC2ContainerServiceBackend, *args, **kwargs):
    tasks = fn(self, *args, **kwargs)
    for task in tasks:
        TASK_RUNNER.launch(self, task)
    return tasks


@patch(EC2ContainerServiceBackend.start_task)
def _start_task(fn, self: EC2ContainerServiceBackend, *args, **kwargs):
    tasks = fn(self, *args, **kwargs)
    for task in tasks:
        TASK_RUNNER.launch(self, task)
    return tasks


@patch(EC2ContainerServiceBackend.stop_task)
def _stop_task(fn, self: EC2ContainerServiceBackend, cluster_str: str, task_str: str, reason: str):
    task_id = task_str.split("/")[-1]
    for task in self.tasks.get(cluster_str.split("/")[-1], {}).values():
        if task.task_arn.endswith(task_id) and task.desired_status == "STOPPED":
            # AWS returns a task that has already stopped without changing it
            return task
    task = fn(self, cluster_str, task_str, reason)
    TASK_RUNNER.stop(task.task_arn, reason or "Task stopped by user", "UserInitiated")
    return task


@patch(EC2ContainerServiceBackend.create_service)
def _create_service(fn, self: EC2ContainerServiceBackend, *args, **kwargs):
    service = fn(self, *args, **kwargs)
    if TASK_RUNNER.enabled:
        # the monitor loop starts the service's tasks; the counts show the real state
        service.running_count = 0
        service.pending_count = 0
        TASK_RUNNER.ensure_started()
    return service


@patch(EC2ContainerServiceBackend.update_service)
def _update_service(fn, self: EC2ContainerServiceBackend, *args, **kwargs):
    service = fn(self, *args, **kwargs)
    TASK_RUNNER.ensure_started()
    return service


@patch(EC2ContainerServiceBackend.list_tasks)
def _list_tasks(fn, self: EC2ContainerServiceBackend, *args, **kwargs):
    tasks = fn(self, *args, **kwargs)
    # Moto's response handler passes the arguments by position:
    # cluster_str, container_instance, family, started_by, service_name, desiredStatus
    service_name = kwargs.get("service_name", args[4] if len(args) > 4 else None)
    if service_name:
        # Moto ignores this filter; tasks of a service have the group "service:<name>"
        group = "service:" + service_name.split("/")[-1]
        tasks = [t for t in tasks if getattr(t, "group", None) == group]
    return tasks


def _grace_period(request: dict) -> int | None:
    value = request.get("healthCheckGracePeriodSeconds")
    return int(value) if value is not None else None


def _add_grace_period(service: dict | None) -> None:
    """Moto drops healthCheckGracePeriodSeconds; it is kept here and returned, as in AWS."""
    if not service:
        return
    from moto.ecs.models import ecs_backends

    for regions in ecs_backends.values():
        for backend in regions.values():
            stored = next(
                (s for s in backend.services.values() if s.arn == service.get("serviceArn")), None
            )
            if stored is not None:
                grace = getattr(stored, "_mocksy_health_check_grace_period", None)
                if grace is not None:
                    service["healthCheckGracePeriodSeconds"] = grace
                return


def _store_grace_period(context, service_arn: str | None, grace: int | None) -> None:
    if grace is None or not service_arn:
        return
    backend = ecs_backends[context.account_id][context.region]
    for stored in backend.services.values():
        if stored.arn == service_arn:
            stored._mocksy_health_check_grace_period = grace


class EcsProvider(EcsApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(ecs_backends)

    @handler("CreateService", expand=False)
    def create_service(self, context: RequestContext, request: dict):
        response = call_moto(context)
        service = response.get("service") or {}
        _store_grace_period(context, service.get("serviceArn"), _grace_period(request))
        _add_grace_period(service)
        return response

    @handler("UpdateService", expand=False)
    def update_service(self, context: RequestContext, request: dict):
        response = call_moto(context)
        service = response.get("service") or {}
        _store_grace_period(context, service.get("serviceArn"), _grace_period(request))
        _add_grace_period(service)
        return response

    @handler("DescribeServices", expand=False)
    def describe_services(self, context: RequestContext, request: dict):
        response = call_moto(context)
        for service in response.get("services") or []:
            _add_grace_period(service)
        return response

    def on_before_stop(self):
        TASK_RUNNER.shutdown()

    def on_before_state_reset(self):
        TASK_RUNNER.shutdown()
