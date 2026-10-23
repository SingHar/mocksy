"""Application Auto Scaling provider.

Operations are handled by Moto through the MotoFallbackDispatcher. Scaling
policies for ECS services are applied by ``scaler`` (issue #5, phase 2), which
also records the scaling activities that DescribeScalingActivities returns.

Moto does not implement DescribeScalingActivities, TagResource, UntagResource
or ListTagsForResource (OpenTofu/Terraform call the last one for every
scalable target); the provider implements them.
"""

import threading

from moto.applicationautoscaling.models import (
    ApplicationAutoscalingBackend,
    applicationautoscaling_backends,
)

from localstack.aws.api import RequestContext, handler
from localstack.aws.api.application_autoscaling import (
    AmazonResourceName,
    ApplicationAutoscalingApi,
    DescribeScalingActivitiesResponse,
    IncludeNotScaledActivities,
    ListTagsForResourceResponse,
    MaxResults,
    RegisterScalableTargetRequest,
    RegisterScalableTargetResponse,
    ResourceIdMaxLen1600,
    ResourceNotFoundException,
    ScalableDimension,
    ServiceNamespace,
    TagKeyList,
    TagMap,
    TagResourceResponse,
    UntagResourceResponse,
    XmlString,
)
from localstack.services.application_autoscaling.scaler import SCALER
from localstack.services.moto import call_moto
from localstack.services.plugins import ServiceLifecycleHook
from localstack.state import StateVisitor
from localstack.utils.patch import patch


@patch(ApplicationAutoscalingBackend.register_scalable_target)
def _register_scalable_target(fn, self, *args, **kwargs):
    target = fn(self, *args, **kwargs)
    SCALER.ensure_started()
    return target


@patch(ApplicationAutoscalingBackend.put_scaling_policy)
def _put_scaling_policy(fn, self, *args, **kwargs):
    policy = fn(self, *args, **kwargs)
    SCALER.ensure_started()
    return policy


class ApplicationAutoscalingProvider(ApplicationAutoscalingApi, ServiceLifecycleHook):
    def __init__(self) -> None:
        self._tags_lock = threading.Lock()
        # scalable target ARN -> tags
        self._tags: dict[str, dict[str, str]] = {}

    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(applicationautoscaling_backends)

    def on_before_stop(self):
        SCALER.shutdown()

    def on_before_state_reset(self):
        SCALER.shutdown()
        with self._tags_lock:
            self._tags.clear()

    # ------------------------------------------------------------------ tags

    @staticmethod
    def _target_exists(context: RequestContext, arn: str) -> bool:
        backend = applicationautoscaling_backends[context.account_id][context.region]
        return any(
            target.arn == arn for targets in backend.targets.values() for target in targets.values()
        )

    @handler("RegisterScalableTarget", expand=False)
    def register_scalable_target(
        self, context: RequestContext, request: RegisterScalableTargetRequest
    ) -> RegisterScalableTargetResponse:
        response = call_moto(context)
        arn = response.get("ScalableTargetARN")
        if arn and request.get("Tags"):
            with self._tags_lock:
                self._tags.setdefault(arn, {}).update(request["Tags"])
        return response

    def list_tags_for_resource(
        self, context: RequestContext, resource_arn: AmazonResourceName, **kwargs
    ) -> ListTagsForResourceResponse:
        if not self._target_exists(context, resource_arn):
            raise ResourceNotFoundException(f"No scalable target found for ARN {resource_arn}")
        with self._tags_lock:
            return ListTagsForResourceResponse(Tags=dict(self._tags.get(resource_arn, {})))

    def tag_resource(
        self, context: RequestContext, resource_arn: AmazonResourceName, tags: TagMap, **kwargs
    ) -> TagResourceResponse:
        if not self._target_exists(context, resource_arn):
            raise ResourceNotFoundException(f"No scalable target found for ARN {resource_arn}")
        with self._tags_lock:
            self._tags.setdefault(resource_arn, {}).update(tags or {})
        return TagResourceResponse()

    def untag_resource(
        self,
        context: RequestContext,
        resource_arn: AmazonResourceName,
        tag_keys: TagKeyList,
        **kwargs,
    ) -> UntagResourceResponse:
        if not self._target_exists(context, resource_arn):
            raise ResourceNotFoundException(f"No scalable target found for ARN {resource_arn}")
        with self._tags_lock:
            current = self._tags.get(resource_arn, {})
            for key in tag_keys or []:
                current.pop(key, None)
        return UntagResourceResponse()

    def describe_scaling_activities(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600 | None = None,
        scalable_dimension: ScalableDimension | None = None,
        max_results: MaxResults | None = None,
        next_token: XmlString | None = None,
        include_not_scaled_activities: IncludeNotScaledActivities | None = None,
        **kwargs,
    ) -> DescribeScalingActivitiesResponse:
        activities = SCALER.activities(
            context.account_id, context.region, service_namespace, resource_id
        )
        if scalable_dimension:
            activities = [a for a in activities if a["ScalableDimension"] == scalable_dimension]
        start = int(next_token) if next_token and next_token.isdigit() else 0
        limit = max_results or 50
        page = activities[start : start + limit]
        response = DescribeScalingActivitiesResponse(ScalingActivities=page)
        if start + limit < len(activities):
            response["NextToken"] = str(start + limit)
        return response
