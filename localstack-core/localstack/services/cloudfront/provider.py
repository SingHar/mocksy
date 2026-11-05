"""CloudFront provider.

Operations are handled by Moto through the MotoFallbackDispatcher. Each
distribution is served on ``<id>.cloudfront.<LOCALSTACK_HOST host>`` and
forwards requests to its origins (see ``edge``).

Fixes on top of Moto:
- Moto returns the text "None" for cache behaviour policy IDs that were not
  set (CachePolicyId, OriginRequestPolicyId, ResponseHeadersPolicyId). AWS
  leaves them out. The provider removes these values.
- Moto returns ``SSLSupportMethod = sni-only`` for distributions that use the
  default CloudFront certificate. AWS leaves it out in that case.
- Moto drops ``CustomErrorResponses`` (its response template for them is also
  invalid). The provider keeps them from the request and returns them.
- Moto stores 0 for unset ``DefaultTTL`` and ``MaxTTL`` of legacy cache
  settings (``ForwardedValues``). AWS uses 86400 and 31536000.
The first three differences make OpenTofu/Terraform show a change on every plan.
"""

import copy
import threading
from typing import Any

from moto.cloudfront.models import (
    CloudFrontBackend,
    DefaultCacheBehaviour,
    Distribution,
    cloudfront_backends,
)

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
from localstack.services.cloudfront.edge import (
    CLOUDFRONT_EDGE,
    HOST_PATTERN,
    distribution_domain,
)
from localstack.services.edge import ROUTER
from localstack.services.moto import call_moto
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch

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


# distribution ID -> CustomErrorResponses of the last create or update request
_custom_error_responses: dict[str, dict[str, Any]] = {}
_custom_error_lock = threading.Lock()


def _remember_error_responses(result: dict[str, Any], config: dict[str, Any] | None) -> None:
    distribution_id = (result.get("Distribution") or {}).get("Id")
    if not distribution_id or config is None:
        return
    responses = config.get("CustomErrorResponses") or {"Quantity": 0}
    with _custom_error_lock:
        _custom_error_responses[distribution_id] = copy.deepcopy(responses)


def _add_error_responses(distribution_id: str | None, config: dict[str, Any] | None) -> None:
    if not distribution_id or config is None:
        return
    with _custom_error_lock:
        responses = _custom_error_responses.get(distribution_id)
    if responses is not None:
        config["CustomErrorResponses"] = copy.deepcopy(responses)


def _clean_distribution_result(
    result: dict[str, Any], distribution_id: str | None = None
) -> dict[str, Any]:
    distribution = result.get("Distribution") or {}
    distribution_id = distribution_id or distribution.get("Id")
    _clean_distribution_config(distribution.get("DistributionConfig"))
    _clean_distribution_config(result.get("DistributionConfig"))
    _add_error_responses(distribution_id, distribution.get("DistributionConfig"))
    _add_error_responses(distribution_id, result.get("DistributionConfig"))
    return result


@patch(DefaultCacheBehaviour.__init__)
def _cache_behaviour_init(fn, self: DefaultCacheBehaviour, config: dict[str, Any]):
    fn(self, config)
    if config.get("ForwardedValues") is not None:
        # AWS defaults for legacy cache settings
        if config.get("DefaultTTL") in (None, ""):
            self.default_ttl = 86400
        if config.get("MaxTTL") in (None, ""):
            self.max_ttl = 31536000


@patch(Distribution.__init__)
def _distribution_init(fn, self: Distribution, *args, **kwargs):
    fn(self, *args, **kwargs)
    # requests to this domain on mocksy's gateway reach the distribution
    self.domain_name = distribution_domain(self.distribution_id)


@patch(CloudFrontBackend.create_invalidation)
def _create_invalidation(fn, self: CloudFrontBackend, dist_id: str, paths: Any, caller_ref: str):
    invalidation = fn(self, dist_id, paths, caller_ref)
    CLOUDFRONT_EDGE.cache.invalidate(dist_id, _invalidation_paths(paths))
    return invalidation


@patch(CloudFrontBackend.update_distribution)
def _update_distribution(fn, self: CloudFrontBackend, dist_config: Any, _id: str, if_match: Any):
    result = fn(self, dist_config, _id, if_match)
    # cached responses may belong to the old behaviours or origins
    CLOUDFRONT_EDGE.cache.clear(_id)
    return result


@patch(CloudFrontBackend.delete_distribution)
def _delete_distribution(fn, self: CloudFrontBackend, distribution_id: str, if_match: Any):
    result = fn(self, distribution_id, if_match)
    CLOUDFRONT_EDGE.cache.clear(distribution_id)
    with _custom_error_lock:
        _custom_error_responses.pop(distribution_id, None)
    return result


def _invalidation_paths(paths: Any) -> list[str]:
    """Moto passes a list of paths (or a single path)."""
    if isinstance(paths, str):
        return [paths]
    if isinstance(paths, dict):
        items = paths.get("Items") or []
        items = items.get("Path", []) if isinstance(items, dict) else items
        return [items] if isinstance(items, str) else list(items)
    return list(paths or [])


class CloudfrontProvider(CloudfrontApi, ServiceLifecycleHook):
    def __init__(self) -> None:
        self._rules = []

    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(cloudfront_backends)

    def on_after_init(self):
        self._rules = [
            ROUTER.add(
                path="/",
                host=HOST_PATTERN,
                endpoint=CLOUDFRONT_EDGE,
                defaults={"path": ""},
                strict_slashes=False,
            ),
            ROUTER.add(
                path="/<path:path>",
                host=HOST_PATTERN,
                endpoint=CLOUDFRONT_EDGE,
                strict_slashes=False,
            ),
        ]

    def on_before_stop(self):
        for rule in self._rules:
            ROUTER.remove(rule)
        self._rules = []

    def on_before_state_reset(self):
        CLOUDFRONT_EDGE.cache.clear()
        with _custom_error_lock:
            _custom_error_responses.clear()

    @handler("CreateDistribution", expand=False)
    def create_distribution(
        self, context: RequestContext, request: CreateDistributionRequest
    ) -> CreateDistributionResult:
        result = call_moto(context)
        _remember_error_responses(result, request.get("DistributionConfig"))
        return _clean_distribution_result(result)

    @handler("CreateDistributionWithTags", expand=False)
    def create_distribution_with_tags(
        self, context: RequestContext, request: CreateDistributionWithTagsRequest
    ) -> CreateDistributionWithTagsResult:
        result = call_moto(context)
        config = (request.get("DistributionConfigWithTags") or {}).get("DistributionConfig")
        _remember_error_responses(result, config)
        return _clean_distribution_result(result)

    @handler("GetDistribution", expand=False)
    def get_distribution(
        self, context: RequestContext, request: GetDistributionRequest
    ) -> GetDistributionResult:
        return _clean_distribution_result(call_moto(context))

    @handler("GetDistributionConfig", expand=False)
    def get_distribution_config(
        self, context: RequestContext, request: GetDistributionConfigRequest
    ) -> GetDistributionConfigResult:
        return _clean_distribution_result(call_moto(context), request.get("Id"))

    @handler("UpdateDistribution", expand=False)
    def update_distribution(
        self, context: RequestContext, request: UpdateDistributionRequest
    ) -> UpdateDistributionResult:
        result = call_moto(context)
        _remember_error_responses(result, request.get("DistributionConfig"))
        return _clean_distribution_result(result)
