"""CloudFront provider.

Phase 1: operations are handled by Moto through the MotoFallbackDispatcher.
Distributions are recorded but requests are not forwarded to origins yet
(see issue #4, phase 2).

Fixes on top of Moto:
- Moto returns the text "None" for cache behaviour policy IDs that were not
  set (CachePolicyId, OriginRequestPolicyId, ResponseHeadersPolicyId). AWS
  leaves them out. The provider removes these values.
- Moto returns ``SSLSupportMethod = sni-only`` for distributions that use the
  default CloudFront certificate. AWS leaves it out in that case.
Both differences make OpenTofu/Terraform show a change on every plan.
"""

from typing import Any

from moto.cloudfront.models import cloudfront_backends

from localstack.aws.api import RequestContext, handler
from localstack.aws.api.cloudfront import (
    CloudfrontApi,
    CreateDistributionRequest,
    CreateDistributionResult,
    CreateDistributionWithTagsRequest,
    CreateDistributionWithTagsResult,
    GetDistributionConfigRequest,
    GetDistributionConfigResult,
    GetDistributionRequest,
    GetDistributionResult,
    UpdateDistributionRequest,
    UpdateDistributionResult,
)
from localstack.services.moto import call_moto
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor

_OPTIONAL_POLICY_IDS = ("CachePolicyId", "OriginRequestPolicyId", "ResponseHeadersPolicyId")
_UNSET_VALUES = ("None", "")


def _clean_cache_behavior(behavior: dict[str, Any] | None) -> None:
    if not behavior:
        return
    for key in _OPTIONAL_POLICY_IDS:
        if behavior.get(key) in _UNSET_VALUES:
            behavior.pop(key, None)


def _clean_distribution_config(config: dict[str, Any] | None) -> None:
    """Remove values that Moto adds but AWS does not return. Changes ``config`` in place."""
    if not config:
        return
    _clean_cache_behavior(config.get("DefaultCacheBehavior"))
    for behavior in (config.get("CacheBehaviors") or {}).get("Items") or []:
        _clean_cache_behavior(behavior)

    certificate = config.get("ViewerCertificate")
    if (
        certificate
        and certificate.get("CloudFrontDefaultCertificate")
        and not certificate.get("ACMCertificateArn")
        and not certificate.get("IAMCertificateId")
    ):
        certificate.pop("SSLSupportMethod", None)


def _clean_distribution_result(result: dict[str, Any]) -> dict[str, Any]:
    distribution = result.get("Distribution") or {}
    _clean_distribution_config(distribution.get("DistributionConfig"))
    _clean_distribution_config(result.get("DistributionConfig"))
    return result


class CloudfrontProvider(CloudfrontApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(cloudfront_backends)

    @handler("CreateDistribution", expand=False)
    def create_distribution(
        self, context: RequestContext, request: CreateDistributionRequest
    ) -> CreateDistributionResult:
        return _clean_distribution_result(call_moto(context))

    @handler("CreateDistributionWithTags", expand=False)
    def create_distribution_with_tags(
        self, context: RequestContext, request: CreateDistributionWithTagsRequest
    ) -> CreateDistributionWithTagsResult:
        return _clean_distribution_result(call_moto(context))

    @handler("GetDistribution", expand=False)
    def get_distribution(
        self, context: RequestContext, request: GetDistributionRequest
    ) -> GetDistributionResult:
        return _clean_distribution_result(call_moto(context))

    @handler("GetDistributionConfig", expand=False)
    def get_distribution_config(
        self, context: RequestContext, request: GetDistributionConfigRequest
    ) -> GetDistributionConfigResult:
        return _clean_distribution_result(call_moto(context))

    @handler("UpdateDistribution", expand=False)
    def update_distribution(
        self, context: RequestContext, request: UpdateDistributionRequest
    ) -> UpdateDistributionResult:
        return _clean_distribution_result(call_moto(context))
