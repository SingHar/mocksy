"""ELBv2 provider (Application Load Balancer).

Operations are handled by Moto through the MotoFallbackDispatcher. Load
balancers serve HTTP and HTTPS through ``data_plane`` (issue #14):
``DNSName`` is a mocksy domain, listeners route requests to targets,
and ``DescribeTargetHealth`` shows the result of real health checks.
"""

from moto.elbv2.models import ELBv2Backend, FakeHealthStatus, FakeTargetGroup, elbv2_backends

from localstack.aws.api.elbv2 import Elbv2Api
from localstack.services.edge import ROUTER
from localstack.services.elbv2.data_plane import DATA_PLANE, HOST_PATTERN, load_balancer_domain
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch


@patch(ELBv2Backend.create_load_balancer)
def _create_load_balancer(fn, self: ELBv2Backend, *args, **kwargs):
    lb = fn(self, *args, **kwargs)
    lb_id = lb.arn.rsplit("/", 1)[-1]
    domain = load_balancer_domain(lb.name, lb_id, self.region_name)
    lb.dns_name = f"internal-{domain}" if lb.scheme == "internal" else domain
    return lb


@patch(ELBv2Backend.create_listener)
def _create_listener(fn, self: ELBv2Backend, *args, **kwargs):
    listener = fn(self, *args, **kwargs)
    DATA_PLANE.ensure_started()
    return listener


@patch(ELBv2Backend.register_targets)
def _register_targets(fn, self: ELBv2Backend, *args, **kwargs):
    result = fn(self, *args, **kwargs)
    DATA_PLANE.ensure_started()
    return result


@patch(ELBv2Backend.delete_target_group)
def _delete_target_group(fn, self: ELBv2Backend, target_group_arn: str, *args, **kwargs):
    result = fn(self, target_group_arn, *args, **kwargs)
    DATA_PLANE.forget_target_group(target_group_arn)
    return result


@patch(FakeTargetGroup.health_for)
def _health_for(fn, self: FakeTargetGroup, target, ec2_backend):
    registered = self.targets.get(target["Id"])
    if registered is not None:
        backend = elbv2_backends[self.account_id][self.region_name]
        if self.arn not in DATA_PLANE.target_groups_in_use(backend):
            # as in AWS: no listener sends traffic to this target group
            return FakeHealthStatus(
                target["Id"],
                target.get("Port") or registered.get("Port") or self.port,
                self.health_check_port,
                "unused",
                "Target.NotInUse",
                "Target group is not configured to receive traffic from the load balancer",
            )
        port = target.get("Port") or registered.get("Port") or self.port
        state = DATA_PLANE.target_health(self, target["Id"], port)
        if state is not None:
            return FakeHealthStatus(
                target["Id"],
                port,
                self.health_check_port,
                state.state,
                state.reason,
                state.description,
            )
    return fn(self, target, ec2_backend)


class Elbv2Provider(Elbv2Api, ServiceLifecycleHook):
    def __init__(self) -> None:
        self._rules = []

    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(elbv2_backends)

    def on_after_init(self):
        self._rules = [
            ROUTER.add(
                path="/",
                host=HOST_PATTERN,
                endpoint=DATA_PLANE,
                defaults={"path": ""},
                strict_slashes=False,
            ),
            ROUTER.add(
                path="/<path:path>",
                host=HOST_PATTERN,
                endpoint=DATA_PLANE,
                strict_slashes=False,
            ),
        ]

    def on_before_stop(self):
        for rule in self._rules:
            ROUTER.remove(rule)
        self._rules = []
        DATA_PLANE.shutdown()

    def on_before_state_reset(self):
        DATA_PLANE.shutdown()
