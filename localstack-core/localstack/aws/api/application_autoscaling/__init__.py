from datetime import datetime
from enum import StrEnum
from typing import TypedDict

from localstack.aws.api import RequestContext, ServiceException, ServiceRequest, handler

AmazonResourceName = str
Cooldown = int
DisableScaleIn = bool
ErrorMessage = str
ExceptionMessage = str
Expression = str
Id = str
IncludeNotScaledActivities = bool
MaxResults = int
MetricDimensionName = str
MetricDimensionValue = str
MetricName = str
MetricNamespace = str
MetricScale = float
MetricUnit = str
MinAdjustmentMagnitude = int
PolicyName = str
PredictiveScalingMaxCapacityBuffer = int
PredictiveScalingMetricDimensionName = str
PredictiveScalingMetricDimensionValue = str
PredictiveScalingMetricName = str
PredictiveScalingMetricNamespace = str
PredictiveScalingMetricType = str
PredictiveScalingMetricUnit = str
PredictiveScalingSchedulingBufferTime = int
ResourceCapacity = int
ResourceId = str
ResourceIdMaxLen1600 = str
ResourceLabel = str
ReturnData = bool
ScalingAdjustment = int
ScalingSuspended = bool
ScheduledActionName = str
TagKey = str
TagValue = str
TargetTrackingMetricDimensionName = str
TargetTrackingMetricDimensionValue = str
TargetTrackingMetricName = str
TargetTrackingMetricNamespace = str
TargetTrackingMetricUnit = str
XmlString = str


class AdjustmentType(StrEnum):
    ChangeInCapacity = "ChangeInCapacity"
    PercentChangeInCapacity = "PercentChangeInCapacity"
    ExactCapacity = "ExactCapacity"


class MetricAggregationType(StrEnum):
    Average = "Average"
    Minimum = "Minimum"
    Maximum = "Maximum"


class MetricStatistic(StrEnum):
    Average = "Average"
    Minimum = "Minimum"
    Maximum = "Maximum"
    SampleCount = "SampleCount"
    Sum = "Sum"


class MetricType(StrEnum):
    DynamoDBReadCapacityUtilization = "DynamoDBReadCapacityUtilization"
    DynamoDBWriteCapacityUtilization = "DynamoDBWriteCapacityUtilization"
    ALBRequestCountPerTarget = "ALBRequestCountPerTarget"
    RDSReaderAverageCPUUtilization = "RDSReaderAverageCPUUtilization"
    RDSReaderAverageDatabaseConnections = "RDSReaderAverageDatabaseConnections"
    EC2SpotFleetRequestAverageCPUUtilization = "EC2SpotFleetRequestAverageCPUUtilization"
    EC2SpotFleetRequestAverageNetworkIn = "EC2SpotFleetRequestAverageNetworkIn"
    EC2SpotFleetRequestAverageNetworkOut = "EC2SpotFleetRequestAverageNetworkOut"
    SageMakerVariantInvocationsPerInstance = "SageMakerVariantInvocationsPerInstance"
    ECSServiceAverageCPUUtilization = "ECSServiceAverageCPUUtilization"
    ECSServiceAverageMemoryUtilization = "ECSServiceAverageMemoryUtilization"
    AppStreamAverageCapacityUtilization = "AppStreamAverageCapacityUtilization"
    ComprehendInferenceUtilization = "ComprehendInferenceUtilization"
    LambdaProvisionedConcurrencyUtilization = "LambdaProvisionedConcurrencyUtilization"
    CassandraReadCapacityUtilization = "CassandraReadCapacityUtilization"
    CassandraWriteCapacityUtilization = "CassandraWriteCapacityUtilization"
    KafkaBrokerStorageUtilization = "KafkaBrokerStorageUtilization"
    ElastiCacheEngineCPUUtilization = "ElastiCacheEngineCPUUtilization"
    ElastiCacheDatabaseMemoryUsagePercentage = "ElastiCacheDatabaseMemoryUsagePercentage"
    ElastiCachePrimaryEngineCPUUtilization = "ElastiCachePrimaryEngineCPUUtilization"
    ElastiCacheReplicaEngineCPUUtilization = "ElastiCacheReplicaEngineCPUUtilization"
    ElastiCacheDatabaseMemoryUsageCountedForEvictPercentage = (
        "ElastiCacheDatabaseMemoryUsageCountedForEvictPercentage"
    )
    NeptuneReaderAverageCPUUtilization = "NeptuneReaderAverageCPUUtilization"
    SageMakerVariantProvisionedConcurrencyUtilization = (
        "SageMakerVariantProvisionedConcurrencyUtilization"
    )
    ElastiCacheDatabaseCapacityUsageCountedForEvictPercentage = (
        "ElastiCacheDatabaseCapacityUsageCountedForEvictPercentage"
    )
    SageMakerInferenceComponentInvocationsPerCopy = "SageMakerInferenceComponentInvocationsPerCopy"
    WorkSpacesAverageUserSessionsCapacityUtilization = (
        "WorkSpacesAverageUserSessionsCapacityUtilization"
    )
    SageMakerInferenceComponentConcurrentRequestsPerCopyHighResolution = (
        "SageMakerInferenceComponentConcurrentRequestsPerCopyHighResolution"
    )
    SageMakerVariantConcurrentRequestsPerModelHighResolution = (
        "SageMakerVariantConcurrentRequestsPerModelHighResolution"
    )


class PolicyType(StrEnum):
    StepScaling = "StepScaling"
    TargetTrackingScaling = "TargetTrackingScaling"
    PredictiveScaling = "PredictiveScaling"


class PredictiveScalingMaxCapacityBreachBehavior(StrEnum):
    HonorMaxCapacity = "HonorMaxCapacity"
    IncreaseMaxCapacity = "IncreaseMaxCapacity"


class PredictiveScalingMode(StrEnum):
    ForecastOnly = "ForecastOnly"
    ForecastAndScale = "ForecastAndScale"


class ScalableDimension(StrEnum):
    ecs_service_DesiredCount = "ecs:service:DesiredCount"
    ec2_spot_fleet_request_TargetCapacity = "ec2:spot-fleet-request:TargetCapacity"
    elasticmapreduce_instancegroup_InstanceCount = "elasticmapreduce:instancegroup:InstanceCount"
    appstream_fleet_DesiredCapacity = "appstream:fleet:DesiredCapacity"
    dynamodb_table_ReadCapacityUnits = "dynamodb:table:ReadCapacityUnits"
    dynamodb_table_WriteCapacityUnits = "dynamodb:table:WriteCapacityUnits"
    dynamodb_index_ReadCapacityUnits = "dynamodb:index:ReadCapacityUnits"
    dynamodb_index_WriteCapacityUnits = "dynamodb:index:WriteCapacityUnits"
    rds_cluster_ReadReplicaCount = "rds:cluster:ReadReplicaCount"
    sagemaker_variant_DesiredInstanceCount = "sagemaker:variant:DesiredInstanceCount"
    custom_resource_ResourceType_Property = "custom-resource:ResourceType:Property"
    comprehend_document_classifier_endpoint_DesiredInferenceUnits = (
        "comprehend:document-classifier-endpoint:DesiredInferenceUnits"
    )
    comprehend_entity_recognizer_endpoint_DesiredInferenceUnits = (
        "comprehend:entity-recognizer-endpoint:DesiredInferenceUnits"
    )
    lambda_function_ProvisionedConcurrency = "lambda:function:ProvisionedConcurrency"
    cassandra_table_ReadCapacityUnits = "cassandra:table:ReadCapacityUnits"
    cassandra_table_WriteCapacityUnits = "cassandra:table:WriteCapacityUnits"
    kafka_broker_storage_VolumeSize = "kafka:broker-storage:VolumeSize"
    elasticache_cache_cluster_Nodes = "elasticache:cache-cluster:Nodes"
    elasticache_replication_group_NodeGroups = "elasticache:replication-group:NodeGroups"
    elasticache_replication_group_Replicas = "elasticache:replication-group:Replicas"
    neptune_cluster_ReadReplicaCount = "neptune:cluster:ReadReplicaCount"
    sagemaker_variant_DesiredProvisionedConcurrency = (
        "sagemaker:variant:DesiredProvisionedConcurrency"
    )
    sagemaker_inference_component_DesiredCopyCount = (
        "sagemaker:inference-component:DesiredCopyCount"
    )
    workspaces_workspacespool_DesiredUserSessions = "workspaces:workspacespool:DesiredUserSessions"


class ScalingActivityStatusCode(StrEnum):
    Pending = "Pending"
    InProgress = "InProgress"
    Successful = "Successful"
    Overridden = "Overridden"
    Unfulfilled = "Unfulfilled"
    Failed = "Failed"


class ServiceNamespace(StrEnum):
    ecs = "ecs"
    elasticmapreduce = "elasticmapreduce"
    ec2 = "ec2"
    appstream = "appstream"
    dynamodb = "dynamodb"
    rds = "rds"
    sagemaker = "sagemaker"
    custom_resource = "custom-resource"
    comprehend = "comprehend"
    lambda_ = "lambda"
    cassandra = "cassandra"
    kafka = "kafka"
    elasticache = "elasticache"
    neptune = "neptune"
    workspaces = "workspaces"


class ConcurrentUpdateException(ServiceException):
    code: str = "ConcurrentUpdateException"
    sender_fault: bool = False
    status_code: int = 400


class FailedResourceAccessException(ServiceException):
    code: str = "FailedResourceAccessException"
    sender_fault: bool = False
    status_code: int = 400


class InternalServiceException(ServiceException):
    code: str = "InternalServiceException"
    sender_fault: bool = False
    status_code: int = 400


class InvalidNextTokenException(ServiceException):
    code: str = "InvalidNextTokenException"
    sender_fault: bool = False
    status_code: int = 400


class LimitExceededException(ServiceException):
    code: str = "LimitExceededException"
    sender_fault: bool = False
    status_code: int = 400


class ObjectNotFoundException(ServiceException):
    code: str = "ObjectNotFoundException"
    sender_fault: bool = False
    status_code: int = 400


class ResourceNotFoundException(ServiceException):
    code: str = "ResourceNotFoundException"
    sender_fault: bool = False
    status_code: int = 400
    ResourceName: AmazonResourceName | None


class TooManyTagsException(ServiceException):
    code: str = "TooManyTagsException"
    sender_fault: bool = False
    status_code: int = 400
    ResourceName: AmazonResourceName | None


class ValidationException(ServiceException):
    code: str = "ValidationException"
    sender_fault: bool = False
    status_code: int = 400


class Alarm(TypedDict, total=False):
    AlarmName: ResourceId
    AlarmARN: ResourceId


Alarms = list[Alarm]
PredictiveScalingForecastValues = list[MetricScale]
TimestampType = datetime
PredictiveScalingForecastTimestamps = list[TimestampType]


class CapacityForecast(TypedDict, total=False):
    Timestamps: PredictiveScalingForecastTimestamps
    Values: PredictiveScalingForecastValues


class TargetTrackingMetricDimension(TypedDict, total=False):
    Name: TargetTrackingMetricDimensionName
    Value: TargetTrackingMetricDimensionValue


TargetTrackingMetricDimensions = list[TargetTrackingMetricDimension]


class TargetTrackingMetric(TypedDict, total=False):
    Dimensions: TargetTrackingMetricDimensions | None
    MetricName: TargetTrackingMetricName | None
    Namespace: TargetTrackingMetricNamespace | None


class TargetTrackingMetricStat(TypedDict, total=False):
    Metric: TargetTrackingMetric
    Stat: XmlString
    Unit: TargetTrackingMetricUnit | None


class TargetTrackingMetricDataQuery(TypedDict, total=False):
    Expression: Expression | None
    Id: Id
    Label: XmlString | None
    MetricStat: TargetTrackingMetricStat | None
    ReturnData: ReturnData | None


TargetTrackingMetricDataQueries = list[TargetTrackingMetricDataQuery]


class MetricDimension(TypedDict, total=False):
    Name: MetricDimensionName
    Value: MetricDimensionValue


MetricDimensions = list[MetricDimension]


class CustomizedMetricSpecification(TypedDict, total=False):
    MetricName: MetricName | None
    Namespace: MetricNamespace | None
    Dimensions: MetricDimensions | None
    Statistic: MetricStatistic | None
    Unit: MetricUnit | None
    Metrics: TargetTrackingMetricDataQueries | None


class DeleteScalingPolicyRequest(ServiceRequest):
    PolicyName: ResourceIdMaxLen1600
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension


class DeleteScalingPolicyResponse(TypedDict, total=False):
    pass


class DeleteScheduledActionRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ScheduledActionName: ResourceIdMaxLen1600
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension


class DeleteScheduledActionResponse(TypedDict, total=False):
    pass


class DeregisterScalableTargetRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension


class DeregisterScalableTargetResponse(TypedDict, total=False):
    pass


ResourceIdsMaxLen1600 = list[ResourceIdMaxLen1600]


class DescribeScalableTargetsRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ResourceIds: ResourceIdsMaxLen1600 | None
    ScalableDimension: ScalableDimension | None
    MaxResults: MaxResults | None
    NextToken: XmlString | None


class SuspendedState(TypedDict, total=False):
    DynamicScalingInSuspended: ScalingSuspended | None
    DynamicScalingOutSuspended: ScalingSuspended | None
    ScheduledScalingSuspended: ScalingSuspended | None


class ScalableTarget(TypedDict, total=False):
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    MinCapacity: ResourceCapacity
    MaxCapacity: ResourceCapacity
    PredictedCapacity: ResourceCapacity | None
    RoleARN: ResourceIdMaxLen1600
    CreationTime: TimestampType
    SuspendedState: SuspendedState | None
    ScalableTargetARN: XmlString | None


ScalableTargets = list[ScalableTarget]


class DescribeScalableTargetsResponse(TypedDict, total=False):
    ScalableTargets: ScalableTargets | None
    NextToken: XmlString | None


class DescribeScalingActivitiesRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600 | None
    ScalableDimension: ScalableDimension | None
    MaxResults: MaxResults | None
    NextToken: XmlString | None
    IncludeNotScaledActivities: IncludeNotScaledActivities | None


class NotScaledReason(TypedDict, total=False):
    Code: XmlString
    MaxCapacity: ResourceCapacity | None
    MinCapacity: ResourceCapacity | None
    CurrentCapacity: ResourceCapacity | None


NotScaledReasons = list[NotScaledReason]


class ScalingActivity(TypedDict, total=False):
    ActivityId: ResourceId
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    Description: XmlString
    Cause: XmlString
    StartTime: TimestampType
    EndTime: TimestampType | None
    StatusCode: ScalingActivityStatusCode
    StatusMessage: XmlString | None
    Details: XmlString | None
    NotScaledReasons: NotScaledReasons | None


ScalingActivities = list[ScalingActivity]


class DescribeScalingActivitiesResponse(TypedDict, total=False):
    ScalingActivities: ScalingActivities | None
    NextToken: XmlString | None


class DescribeScalingPoliciesRequest(ServiceRequest):
    PolicyNames: ResourceIdsMaxLen1600 | None
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600 | None
    ScalableDimension: ScalableDimension | None
    MaxResults: MaxResults | None
    NextToken: XmlString | None


class PredictiveScalingMetricDimension(TypedDict, total=False):
    Name: PredictiveScalingMetricDimensionName
    Value: PredictiveScalingMetricDimensionValue


PredictiveScalingMetricDimensions = list[PredictiveScalingMetricDimension]


class PredictiveScalingMetric(TypedDict, total=False):
    Dimensions: PredictiveScalingMetricDimensions | None
    MetricName: PredictiveScalingMetricName | None
    Namespace: PredictiveScalingMetricNamespace | None


class PredictiveScalingMetricStat(TypedDict, total=False):
    Metric: PredictiveScalingMetric
    Stat: XmlString
    Unit: PredictiveScalingMetricUnit | None


class PredictiveScalingMetricDataQuery(TypedDict, total=False):
    Id: Id
    Expression: Expression | None
    MetricStat: PredictiveScalingMetricStat | None
    Label: XmlString | None
    ReturnData: ReturnData | None


PredictiveScalingMetricDataQueries = list[PredictiveScalingMetricDataQuery]


class PredictiveScalingCustomizedMetricSpecification(TypedDict, total=False):
    MetricDataQueries: PredictiveScalingMetricDataQueries


class PredictiveScalingPredefinedLoadMetricSpecification(TypedDict, total=False):
    PredefinedMetricType: PredictiveScalingMetricType
    ResourceLabel: ResourceLabel | None


class PredictiveScalingPredefinedScalingMetricSpecification(TypedDict, total=False):
    PredefinedMetricType: PredictiveScalingMetricType
    ResourceLabel: ResourceLabel | None


class PredictiveScalingPredefinedMetricPairSpecification(TypedDict, total=False):
    PredefinedMetricType: PredictiveScalingMetricType
    ResourceLabel: ResourceLabel | None


class PredictiveScalingMetricSpecification(TypedDict, total=False):
    TargetValue: MetricScale
    PredefinedMetricPairSpecification: PredictiveScalingPredefinedMetricPairSpecification | None
    PredefinedScalingMetricSpecification: (
        PredictiveScalingPredefinedScalingMetricSpecification | None
    )
    PredefinedLoadMetricSpecification: PredictiveScalingPredefinedLoadMetricSpecification | None
    CustomizedScalingMetricSpecification: PredictiveScalingCustomizedMetricSpecification | None
    CustomizedLoadMetricSpecification: PredictiveScalingCustomizedMetricSpecification | None
    CustomizedCapacityMetricSpecification: PredictiveScalingCustomizedMetricSpecification | None


PredictiveScalingMetricSpecifications = list[PredictiveScalingMetricSpecification]


class PredictiveScalingPolicyConfiguration(TypedDict, total=False):
    MetricSpecifications: PredictiveScalingMetricSpecifications
    Mode: PredictiveScalingMode | None
    SchedulingBufferTime: PredictiveScalingSchedulingBufferTime | None
    MaxCapacityBreachBehavior: PredictiveScalingMaxCapacityBreachBehavior | None
    MaxCapacityBuffer: PredictiveScalingMaxCapacityBuffer | None


class PredefinedMetricSpecification(TypedDict, total=False):
    PredefinedMetricType: MetricType
    ResourceLabel: ResourceLabel | None


class TargetTrackingScalingPolicyConfiguration(TypedDict, total=False):
    TargetValue: MetricScale
    PredefinedMetricSpecification: PredefinedMetricSpecification | None
    CustomizedMetricSpecification: CustomizedMetricSpecification | None
    ScaleOutCooldown: Cooldown | None
    ScaleInCooldown: Cooldown | None
    DisableScaleIn: DisableScaleIn | None


class StepAdjustment(TypedDict, total=False):
    MetricIntervalLowerBound: MetricScale | None
    MetricIntervalUpperBound: MetricScale | None
    ScalingAdjustment: ScalingAdjustment


StepAdjustments = list[StepAdjustment]


class StepScalingPolicyConfiguration(TypedDict, total=False):
    AdjustmentType: AdjustmentType | None
    StepAdjustments: StepAdjustments | None
    MinAdjustmentMagnitude: MinAdjustmentMagnitude | None
    Cooldown: Cooldown | None
    MetricAggregationType: MetricAggregationType | None


class ScalingPolicy(TypedDict, total=False):
    PolicyARN: ResourceIdMaxLen1600
    PolicyName: PolicyName
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    PolicyType: PolicyType
    StepScalingPolicyConfiguration: StepScalingPolicyConfiguration | None
    TargetTrackingScalingPolicyConfiguration: TargetTrackingScalingPolicyConfiguration | None
    PredictiveScalingPolicyConfiguration: PredictiveScalingPolicyConfiguration | None
    Alarms: Alarms | None
    CreationTime: TimestampType


ScalingPolicies = list[ScalingPolicy]


class DescribeScalingPoliciesResponse(TypedDict, total=False):
    ScalingPolicies: ScalingPolicies | None
    NextToken: XmlString | None


class DescribeScheduledActionsRequest(ServiceRequest):
    ScheduledActionNames: ResourceIdsMaxLen1600 | None
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600 | None
    ScalableDimension: ScalableDimension | None
    MaxResults: MaxResults | None
    NextToken: XmlString | None


class ScalableTargetAction(TypedDict, total=False):
    MinCapacity: ResourceCapacity | None
    MaxCapacity: ResourceCapacity | None


class ScheduledAction(TypedDict, total=False):
    ScheduledActionName: ScheduledActionName
    ScheduledActionARN: ResourceIdMaxLen1600
    ServiceNamespace: ServiceNamespace
    Schedule: ResourceIdMaxLen1600
    Timezone: ResourceIdMaxLen1600 | None
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension | None
    StartTime: TimestampType | None
    EndTime: TimestampType | None
    ScalableTargetAction: ScalableTargetAction | None
    CreationTime: TimestampType


ScheduledActions = list[ScheduledAction]


class DescribeScheduledActionsResponse(TypedDict, total=False):
    ScheduledActions: ScheduledActions | None
    NextToken: XmlString | None


class GetPredictiveScalingForecastRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    PolicyName: PolicyName
    StartTime: TimestampType
    EndTime: TimestampType


class LoadForecast(TypedDict, total=False):
    Timestamps: PredictiveScalingForecastTimestamps
    Values: PredictiveScalingForecastValues
    MetricSpecification: PredictiveScalingMetricSpecification


LoadForecasts = list[LoadForecast]


class GetPredictiveScalingForecastResponse(TypedDict, total=False):
    LoadForecast: LoadForecasts | None
    CapacityForecast: CapacityForecast | None
    UpdateTime: TimestampType | None


class ListTagsForResourceRequest(ServiceRequest):
    ResourceARN: AmazonResourceName


TagMap = dict[TagKey, TagValue]


class ListTagsForResourceResponse(TypedDict, total=False):
    Tags: TagMap | None


class PutScalingPolicyRequest(ServiceRequest):
    PolicyName: PolicyName
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    PolicyType: PolicyType | None
    StepScalingPolicyConfiguration: StepScalingPolicyConfiguration | None
    TargetTrackingScalingPolicyConfiguration: TargetTrackingScalingPolicyConfiguration | None
    PredictiveScalingPolicyConfiguration: PredictiveScalingPolicyConfiguration | None


class PutScalingPolicyResponse(TypedDict, total=False):
    PolicyARN: ResourceIdMaxLen1600
    Alarms: Alarms | None


class PutScheduledActionRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    Schedule: ResourceIdMaxLen1600 | None
    Timezone: ResourceIdMaxLen1600 | None
    ScheduledActionName: ScheduledActionName
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    StartTime: TimestampType | None
    EndTime: TimestampType | None
    ScalableTargetAction: ScalableTargetAction | None


class PutScheduledActionResponse(TypedDict, total=False):
    pass


class RegisterScalableTargetRequest(ServiceRequest):
    ServiceNamespace: ServiceNamespace
    ResourceId: ResourceIdMaxLen1600
    ScalableDimension: ScalableDimension
    MinCapacity: ResourceCapacity | None
    MaxCapacity: ResourceCapacity | None
    RoleARN: ResourceIdMaxLen1600 | None
    SuspendedState: SuspendedState | None
    Tags: TagMap | None


class RegisterScalableTargetResponse(TypedDict, total=False):
    ScalableTargetARN: XmlString | None


TagKeyList = list[TagKey]


class TagResourceRequest(ServiceRequest):
    ResourceARN: AmazonResourceName
    Tags: TagMap


class TagResourceResponse(TypedDict, total=False):
    pass


class UntagResourceRequest(ServiceRequest):
    ResourceARN: AmazonResourceName
    TagKeys: TagKeyList


class UntagResourceResponse(TypedDict, total=False):
    pass


class ApplicationAutoscalingApi:
    service: str = "application-autoscaling"
    version: str = "2016-02-06"

    @handler("DeleteScalingPolicy")
    def delete_scaling_policy(
        self,
        context: RequestContext,
        policy_name: ResourceIdMaxLen1600,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        **kwargs,
    ) -> DeleteScalingPolicyResponse:
        raise NotImplementedError

    @handler("DeleteScheduledAction")
    def delete_scheduled_action(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        scheduled_action_name: ResourceIdMaxLen1600,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        **kwargs,
    ) -> DeleteScheduledActionResponse:
        raise NotImplementedError

    @handler("DeregisterScalableTarget")
    def deregister_scalable_target(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        **kwargs,
    ) -> DeregisterScalableTargetResponse:
        raise NotImplementedError

    @handler("DescribeScalableTargets")
    def describe_scalable_targets(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        resource_ids: ResourceIdsMaxLen1600 | None = None,
        scalable_dimension: ScalableDimension | None = None,
        max_results: MaxResults | None = None,
        next_token: XmlString | None = None,
        **kwargs,
    ) -> DescribeScalableTargetsResponse:
        raise NotImplementedError

    @handler("DescribeScalingActivities")
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
        raise NotImplementedError

    @handler("DescribeScalingPolicies")
    def describe_scaling_policies(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        policy_names: ResourceIdsMaxLen1600 | None = None,
        resource_id: ResourceIdMaxLen1600 | None = None,
        scalable_dimension: ScalableDimension | None = None,
        max_results: MaxResults | None = None,
        next_token: XmlString | None = None,
        **kwargs,
    ) -> DescribeScalingPoliciesResponse:
        raise NotImplementedError

    @handler("DescribeScheduledActions")
    def describe_scheduled_actions(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        scheduled_action_names: ResourceIdsMaxLen1600 | None = None,
        resource_id: ResourceIdMaxLen1600 | None = None,
        scalable_dimension: ScalableDimension | None = None,
        max_results: MaxResults | None = None,
        next_token: XmlString | None = None,
        **kwargs,
    ) -> DescribeScheduledActionsResponse:
        raise NotImplementedError

    @handler("GetPredictiveScalingForecast")
    def get_predictive_scaling_forecast(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        policy_name: PolicyName,
        start_time: TimestampType,
        end_time: TimestampType,
        **kwargs,
    ) -> GetPredictiveScalingForecastResponse:
        raise NotImplementedError

    @handler("ListTagsForResource")
    def list_tags_for_resource(
        self, context: RequestContext, resource_arn: AmazonResourceName, **kwargs
    ) -> ListTagsForResourceResponse:
        raise NotImplementedError

    @handler("PutScalingPolicy")
    def put_scaling_policy(
        self,
        context: RequestContext,
        policy_name: PolicyName,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        policy_type: PolicyType | None = None,
        step_scaling_policy_configuration: StepScalingPolicyConfiguration | None = None,
        target_tracking_scaling_policy_configuration: TargetTrackingScalingPolicyConfiguration
        | None = None,
        predictive_scaling_policy_configuration: PredictiveScalingPolicyConfiguration | None = None,
        **kwargs,
    ) -> PutScalingPolicyResponse:
        raise NotImplementedError

    @handler("PutScheduledAction")
    def put_scheduled_action(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        scheduled_action_name: ScheduledActionName,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        schedule: ResourceIdMaxLen1600 | None = None,
        timezone: ResourceIdMaxLen1600 | None = None,
        start_time: TimestampType | None = None,
        end_time: TimestampType | None = None,
        scalable_target_action: ScalableTargetAction | None = None,
        **kwargs,
    ) -> PutScheduledActionResponse:
        raise NotImplementedError

    @handler("RegisterScalableTarget")
    def register_scalable_target(
        self,
        context: RequestContext,
        service_namespace: ServiceNamespace,
        resource_id: ResourceIdMaxLen1600,
        scalable_dimension: ScalableDimension,
        min_capacity: ResourceCapacity | None = None,
        max_capacity: ResourceCapacity | None = None,
        role_arn: ResourceIdMaxLen1600 | None = None,
        suspended_state: SuspendedState | None = None,
        tags: TagMap | None = None,
        **kwargs,
    ) -> RegisterScalableTargetResponse:
        raise NotImplementedError

    @handler("TagResource")
    def tag_resource(
        self, context: RequestContext, resource_arn: AmazonResourceName, tags: TagMap, **kwargs
    ) -> TagResourceResponse:
        raise NotImplementedError

    @handler("UntagResource")
    def untag_resource(
        self,
        context: RequestContext,
        resource_arn: AmazonResourceName,
        tag_keys: TagKeyList,
        **kwargs,
    ) -> UntagResourceResponse:
        raise NotImplementedError
