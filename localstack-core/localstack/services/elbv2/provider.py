"""ELBv2 provider (Application Load Balancer).

Phase 1: operations are handled by Moto through the MotoFallbackDispatcher
(see issue #14).
"""

from moto.elbv2.models import elbv2_backends

from localstack.aws.api.elbv2 import Elbv2Api
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor


class Elbv2Provider(Elbv2Api, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(elbv2_backends)
