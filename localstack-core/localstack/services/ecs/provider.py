"""ECS provider.

Phase 1: operations are handled by Moto through the MotoFallbackDispatcher.
Tasks are recorded but no containers run yet (see issue #1, phase 2).

Fixes on top of Moto:
- ``awsvpcConfiguration.securityGroups`` is optional in AWS. When it is missing,
  AWS uses the default security group of the subnet's VPC, and the service and
  task still show the network configuration as it was sent. Moto raises an
  internal error instead. The provider uses the default group inside Moto and
  keeps the stored configuration as sent, so OpenTofu/Terraform shows no change
  on the next plan.
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
from moto.ecs.models import EC2ContainerServiceBackend, Service, Task, ecs_backends

from localstack.aws.api.ecs import EcsApi
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch

LOG = logging.getLogger(__name__)


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


class EcsProvider(EcsApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(ecs_backends)
