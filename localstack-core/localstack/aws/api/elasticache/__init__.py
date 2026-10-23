from datetime import datetime
from enum import StrEnum
from typing import TypedDict

from localstack.aws.api import RequestContext, ServiceException, ServiceRequest, handler

AccessString = str
AllowedNodeGroupId = str
AwsQueryErrorMessage = str
Boolean = bool
BooleanOptional = bool
Double = float
EngineType = str
FilterName = str
FilterValue = str
Integer = int
IntegerOptional = int
String = str
UserGroupId = str
UserId = str
UserName = str


class AZMode(StrEnum):
    single_az = "single-az"
    cross_az = "cross-az"


class AuthTokenUpdateStatus(StrEnum):
    SETTING = "SETTING"
    ROTATING = "ROTATING"


class AuthTokenUpdateStrategyType(StrEnum):
    SET = "SET"
    ROTATE = "ROTATE"
    DELETE = "DELETE"


class AuthenticationType(StrEnum):
    password = "password"
    no_password = "no-password"
    iam = "iam"


class AutomaticFailoverStatus(StrEnum):
    enabled = "enabled"
    disabled = "disabled"
    enabling = "enabling"
    disabling = "disabling"


class ChangeType(StrEnum):
    immediate = "immediate"
    requires_reboot = "requires-reboot"


class ClusterMode(StrEnum):
    enabled = "enabled"
    disabled = "disabled"
    compatible = "compatible"


class DataStorageUnit(StrEnum):
    GB = "GB"


class DataTieringStatus(StrEnum):
    enabled = "enabled"
    disabled = "disabled"


class DestinationType(StrEnum):
    cloudwatch_logs = "cloudwatch-logs"
    kinesis_firehose = "kinesis-firehose"


class InputAuthenticationType(StrEnum):
    password = "password"
    no_password_required = "no-password-required"
    iam = "iam"


class IpDiscovery(StrEnum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"


class LogDeliveryConfigurationStatus(StrEnum):
    active = "active"
    enabling = "enabling"
    modifying = "modifying"
    disabling = "disabling"
    error = "error"


class LogFormat(StrEnum):
    text = "text"
    json = "json"


class LogType(StrEnum):
    slow_log = "slow-log"
    engine_log = "engine-log"


class MultiAZStatus(StrEnum):
    enabled = "enabled"
    disabled = "disabled"


class NetworkType(StrEnum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    dual_stack = "dual_stack"


class NodeUpdateInitiatedBy(StrEnum):
    system = "system"
    customer = "customer"


class NodeUpdateStatus(StrEnum):
    not_applied = "not-applied"
    waiting_to_start = "waiting-to-start"
    in_progress = "in-progress"
    stopping = "stopping"
    stopped = "stopped"
    complete = "complete"


class OutpostMode(StrEnum):
    single_outpost = "single-outpost"
    cross_outpost = "cross-outpost"


class PendingAutomaticFailoverStatus(StrEnum):
    enabled = "enabled"
    disabled = "disabled"


class ServiceUpdateSeverity(StrEnum):
    critical = "critical"
    important = "important"
    medium = "medium"
    low = "low"


class ServiceUpdateStatus(StrEnum):
    available = "available"
    cancelled = "cancelled"
    expired = "expired"


class ServiceUpdateType(StrEnum):
    security_update = "security-update"


class SlaMet(StrEnum):
    yes = "yes"
    no = "no"
    n_a = "n/a"


class SourceType(StrEnum):
    cache_cluster = "cache-cluster"
    cache_parameter_group = "cache-parameter-group"
    cache_security_group = "cache-security-group"
    cache_subnet_group = "cache-subnet-group"
    replication_group = "replication-group"
    serverless_cache = "serverless-cache"
    serverless_cache_snapshot = "serverless-cache-snapshot"
    user = "user"
    user_group = "user-group"


class TransitEncryptionMode(StrEnum):
    preferred = "preferred"
    required = "required"


class UpdateActionStatus(StrEnum):
    not_applied = "not-applied"
    waiting_to_start = "waiting-to-start"
    in_progress = "in-progress"
    stopping = "stopping"
    stopped = "stopped"
    complete = "complete"
    scheduling = "scheduling"
    scheduled = "scheduled"
    not_applicable = "not-applicable"


class APICallRateForCustomerExceededFault(ServiceException):
    code: str = "APICallRateForCustomerExceeded"
    sender_fault: bool = True
    status_code: int = 400


class AuthorizationAlreadyExistsFault(ServiceException):
    code: str = "AuthorizationAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class AuthorizationNotFoundFault(ServiceException):
    code: str = "AuthorizationNotFound"
    sender_fault: bool = True
    status_code: int = 404


class CacheClusterAlreadyExistsFault(ServiceException):
    code: str = "CacheClusterAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class CacheClusterNotFoundFault(ServiceException):
    code: str = "CacheClusterNotFound"
    sender_fault: bool = True
    status_code: int = 404


class CacheParameterGroupAlreadyExistsFault(ServiceException):
    code: str = "CacheParameterGroupAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class CacheParameterGroupNotFoundFault(ServiceException):
    code: str = "CacheParameterGroupNotFound"
    sender_fault: bool = True
    status_code: int = 404


class CacheParameterGroupQuotaExceededFault(ServiceException):
    code: str = "CacheParameterGroupQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class CacheSecurityGroupAlreadyExistsFault(ServiceException):
    code: str = "CacheSecurityGroupAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class CacheSecurityGroupNotFoundFault(ServiceException):
    code: str = "CacheSecurityGroupNotFound"
    sender_fault: bool = True
    status_code: int = 404


class CacheSecurityGroupQuotaExceededFault(ServiceException):
    code: str = "QuotaExceeded.CacheSecurityGroup"
    sender_fault: bool = True
    status_code: int = 400


class CacheSubnetGroupAlreadyExistsFault(ServiceException):
    code: str = "CacheSubnetGroupAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class CacheSubnetGroupInUse(ServiceException):
    code: str = "CacheSubnetGroupInUse"
    sender_fault: bool = True
    status_code: int = 400


class CacheSubnetGroupNotFoundFault(ServiceException):
    code: str = "CacheSubnetGroupNotFoundFault"
    sender_fault: bool = True
    status_code: int = 400


class CacheSubnetGroupQuotaExceededFault(ServiceException):
    code: str = "CacheSubnetGroupQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class CacheSubnetQuotaExceededFault(ServiceException):
    code: str = "CacheSubnetQuotaExceededFault"
    sender_fault: bool = True
    status_code: int = 400


class ClusterQuotaForCustomerExceededFault(ServiceException):
    code: str = "ClusterQuotaForCustomerExceeded"
    sender_fault: bool = True
    status_code: int = 400


class DefaultUserAssociatedToUserGroupFault(ServiceException):
    code: str = "DefaultUserAssociatedToUserGroup"
    sender_fault: bool = True
    status_code: int = 400


class DefaultUserRequired(ServiceException):
    code: str = "DefaultUserRequired"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateUserNameFault(ServiceException):
    code: str = "DuplicateUserName"
    sender_fault: bool = True
    status_code: int = 400


class GlobalReplicationGroupAlreadyExistsFault(ServiceException):
    code: str = "GlobalReplicationGroupAlreadyExistsFault"
    sender_fault: bool = True
    status_code: int = 400


class GlobalReplicationGroupNotFoundFault(ServiceException):
    code: str = "GlobalReplicationGroupNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class InsufficientCacheClusterCapacityFault(ServiceException):
    code: str = "InsufficientCacheClusterCapacity"
    sender_fault: bool = True
    status_code: int = 400


class InvalidARNFault(ServiceException):
    code: str = "InvalidARN"
    sender_fault: bool = True
    status_code: int = 400


class InvalidCacheClusterStateFault(ServiceException):
    code: str = "InvalidCacheClusterState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidCacheParameterGroupStateFault(ServiceException):
    code: str = "InvalidCacheParameterGroupState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidCacheSecurityGroupStateFault(ServiceException):
    code: str = "InvalidCacheSecurityGroupState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidCredentialsException(ServiceException):
    code: str = "InvalidCredentialsException"
    sender_fault: bool = True
    status_code: int = 408


class InvalidGlobalReplicationGroupStateFault(ServiceException):
    code: str = "InvalidGlobalReplicationGroupState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidKMSKeyFault(ServiceException):
    code: str = "InvalidKMSKeyFault"
    sender_fault: bool = True
    status_code: int = 400


class InvalidParameterCombinationException(ServiceException):
    code: str = "InvalidParameterCombination"
    sender_fault: bool = True
    status_code: int = 400


class InvalidParameterValueException(ServiceException):
    code: str = "InvalidParameterValue"
    sender_fault: bool = True
    status_code: int = 400


class InvalidReplicationGroupStateFault(ServiceException):
    code: str = "InvalidReplicationGroupState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidServerlessCacheSnapshotStateFault(ServiceException):
    code: str = "InvalidServerlessCacheSnapshotStateFault"
    sender_fault: bool = True
    status_code: int = 400


class InvalidServerlessCacheStateFault(ServiceException):
    code: str = "InvalidServerlessCacheStateFault"
    sender_fault: bool = True
    status_code: int = 400


class InvalidSnapshotStateFault(ServiceException):
    code: str = "InvalidSnapshotState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidSubnet(ServiceException):
    code: str = "InvalidSubnet"
    sender_fault: bool = True
    status_code: int = 400


class InvalidUserGroupStateFault(ServiceException):
    code: str = "InvalidUserGroupState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidUserStateFault(ServiceException):
    code: str = "InvalidUserState"
    sender_fault: bool = True
    status_code: int = 400


class InvalidVPCNetworkStateFault(ServiceException):
    code: str = "InvalidVPCNetworkStateFault"
    sender_fault: bool = True
    status_code: int = 400


class NoOperationFault(ServiceException):
    code: str = "NoOperationFault"
    sender_fault: bool = True
    status_code: int = 400


class NodeGroupNotFoundFault(ServiceException):
    code: str = "NodeGroupNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class NodeGroupsPerReplicationGroupQuotaExceededFault(ServiceException):
    code: str = "NodeGroupsPerReplicationGroupQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class NodeQuotaForClusterExceededFault(ServiceException):
    code: str = "NodeQuotaForClusterExceeded"
    sender_fault: bool = True
    status_code: int = 400


class NodeQuotaForCustomerExceededFault(ServiceException):
    code: str = "NodeQuotaForCustomerExceeded"
    sender_fault: bool = True
    status_code: int = 400


class ReplicationGroupAlreadyExistsFault(ServiceException):
    code: str = "ReplicationGroupAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class ReplicationGroupAlreadyUnderMigrationFault(ServiceException):
    code: str = "ReplicationGroupAlreadyUnderMigrationFault"
    sender_fault: bool = True
    status_code: int = 400


class ReplicationGroupNotFoundFault(ServiceException):
    code: str = "ReplicationGroupNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class ReplicationGroupNotUnderMigrationFault(ServiceException):
    code: str = "ReplicationGroupNotUnderMigrationFault"
    sender_fault: bool = True
    status_code: int = 400


class ReservedCacheNodeAlreadyExistsFault(ServiceException):
    code: str = "ReservedCacheNodeAlreadyExists"
    sender_fault: bool = True
    status_code: int = 404


class ReservedCacheNodeNotFoundFault(ServiceException):
    code: str = "ReservedCacheNodeNotFound"
    sender_fault: bool = True
    status_code: int = 404


class ReservedCacheNodeQuotaExceededFault(ServiceException):
    code: str = "ReservedCacheNodeQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class ReservedCacheNodesOfferingNotFoundFault(ServiceException):
    code: str = "ReservedCacheNodesOfferingNotFound"
    sender_fault: bool = True
    status_code: int = 404


class ServerlessCacheAlreadyExistsFault(ServiceException):
    code: str = "ServerlessCacheAlreadyExistsFault"
    sender_fault: bool = True
    status_code: int = 400


class ServerlessCacheNotFoundFault(ServiceException):
    code: str = "ServerlessCacheNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class ServerlessCacheQuotaForCustomerExceededFault(ServiceException):
    code: str = "ServerlessCacheQuotaForCustomerExceededFault"
    sender_fault: bool = True
    status_code: int = 400


class ServerlessCacheSnapshotAlreadyExistsFault(ServiceException):
    code: str = "ServerlessCacheSnapshotAlreadyExistsFault"
    sender_fault: bool = True
    status_code: int = 400


class ServerlessCacheSnapshotNotFoundFault(ServiceException):
    code: str = "ServerlessCacheSnapshotNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class ServerlessCacheSnapshotQuotaExceededFault(ServiceException):
    code: str = "ServerlessCacheSnapshotQuotaExceededFault"
    sender_fault: bool = True
    status_code: int = 400


class ServiceLinkedRoleNotFoundFault(ServiceException):
    code: str = "ServiceLinkedRoleNotFoundFault"
    sender_fault: bool = True
    status_code: int = 400


class ServiceUpdateNotFoundFault(ServiceException):
    code: str = "ServiceUpdateNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class SnapshotAlreadyExistsFault(ServiceException):
    code: str = "SnapshotAlreadyExistsFault"
    sender_fault: bool = True
    status_code: int = 400


class SnapshotFeatureNotSupportedFault(ServiceException):
    code: str = "SnapshotFeatureNotSupportedFault"
    sender_fault: bool = True
    status_code: int = 400


class SnapshotNotFoundFault(ServiceException):
    code: str = "SnapshotNotFoundFault"
    sender_fault: bool = True
    status_code: int = 404


class SnapshotQuotaExceededFault(ServiceException):
    code: str = "SnapshotQuotaExceededFault"
    sender_fault: bool = True
    status_code: int = 400


class SubnetInUse(ServiceException):
    code: str = "SubnetInUse"
    sender_fault: bool = True
    status_code: int = 400


class SubnetNotAllowedFault(ServiceException):
    code: str = "SubnetNotAllowedFault"
    sender_fault: bool = True
    status_code: int = 400


class TagNotFoundFault(ServiceException):
    code: str = "TagNotFound"
    sender_fault: bool = True
    status_code: int = 404


class TagQuotaPerResourceExceeded(ServiceException):
    code: str = "TagQuotaPerResourceExceeded"
    sender_fault: bool = True
    status_code: int = 400


class TestFailoverNotAvailableFault(ServiceException):
    code: str = "TestFailoverNotAvailableFault"
    sender_fault: bool = True
    status_code: int = 400


class UserAlreadyExistsFault(ServiceException):
    code: str = "UserAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class UserGroupAlreadyExistsFault(ServiceException):
    code: str = "UserGroupAlreadyExists"
    sender_fault: bool = True
    status_code: int = 400


class UserGroupNotFoundFault(ServiceException):
    code: str = "UserGroupNotFound"
    sender_fault: bool = True
    status_code: int = 404


class UserGroupQuotaExceededFault(ServiceException):
    code: str = "UserGroupQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class UserNotFoundFault(ServiceException):
    code: str = "UserNotFound"
    sender_fault: bool = True
    status_code: int = 404


class UserQuotaExceededFault(ServiceException):
    code: str = "UserQuotaExceeded"
    sender_fault: bool = True
    status_code: int = 400


class Tag(TypedDict, total=False):
    Key: String | None
    Value: String | None


TagList = list[Tag]


class AddTagsToResourceMessage(ServiceRequest):
    ResourceName: String
    Tags: TagList


NodeTypeList = list[String]


class AllowedNodeTypeModificationsMessage(TypedDict, total=False):
    ScaleUpModifications: NodeTypeList | None
    ScaleDownModifications: NodeTypeList | None


class Authentication(TypedDict, total=False):
    Type: AuthenticationType | None
    PasswordCount: IntegerOptional | None


PasswordListInput = list[String]


class AuthenticationMode(TypedDict, total=False):
    Type: InputAuthenticationType | None
    Passwords: PasswordListInput | None


class AuthorizeCacheSecurityGroupIngressMessage(ServiceRequest):
    CacheSecurityGroupName: String
    EC2SecurityGroupName: String
    EC2SecurityGroupOwnerId: String


class EC2SecurityGroup(TypedDict, total=False):
    Status: String | None
    EC2SecurityGroupName: String | None
    EC2SecurityGroupOwnerId: String | None


EC2SecurityGroupList = list[EC2SecurityGroup]


class CacheSecurityGroup(TypedDict, total=False):
    OwnerId: String | None
    CacheSecurityGroupName: String | None
    Description: String | None
    EC2SecurityGroups: EC2SecurityGroupList | None
    ARN: String | None


class AuthorizeCacheSecurityGroupIngressResult(TypedDict, total=False):
    CacheSecurityGroup: CacheSecurityGroup | None


class AvailabilityZone(TypedDict, total=False):
    Name: String | None


AvailabilityZonesList = list[String]
CacheClusterIdList = list[String]
ReplicationGroupIdList = list[String]


class BatchApplyUpdateActionMessage(ServiceRequest):
    ReplicationGroupIds: ReplicationGroupIdList | None
    CacheClusterIds: CacheClusterIdList | None
    ServiceUpdateName: String


class BatchStopUpdateActionMessage(ServiceRequest):
    ReplicationGroupIds: ReplicationGroupIdList | None
    CacheClusterIds: CacheClusterIdList | None
    ServiceUpdateName: String


class KinesisFirehoseDestinationDetails(TypedDict, total=False):
    DeliveryStream: String | None


class CloudWatchLogsDestinationDetails(TypedDict, total=False):
    LogGroup: String | None


class DestinationDetails(TypedDict, total=False):
    CloudWatchLogsDetails: CloudWatchLogsDestinationDetails | None
    KinesisFirehoseDetails: KinesisFirehoseDestinationDetails | None


class LogDeliveryConfiguration(TypedDict, total=False):
    LogType: LogType | None
    DestinationType: DestinationType | None
    DestinationDetails: DestinationDetails | None
    LogFormat: LogFormat | None
    Status: LogDeliveryConfigurationStatus | None
    Message: String | None


LogDeliveryConfigurationList = list[LogDeliveryConfiguration]
TStamp = datetime


class SecurityGroupMembership(TypedDict, total=False):
    SecurityGroupId: String | None
    Status: String | None


SecurityGroupMembershipList = list[SecurityGroupMembership]


class Endpoint(TypedDict, total=False):
    Address: String | None
    Port: Integer | None


class CacheNode(TypedDict, total=False):
    CacheNodeId: String | None
    CacheNodeStatus: String | None
    CacheNodeCreateTime: TStamp | None
    Endpoint: Endpoint | None
    ParameterGroupStatus: String | None
    SourceCacheNodeId: String | None
    CustomerAvailabilityZone: String | None
    CustomerOutpostArn: String | None


CacheNodeList = list[CacheNode]
CacheNodeIdsList = list[String]


class CacheParameterGroupStatus(TypedDict, total=False):
    CacheParameterGroupName: String | None
    ParameterApplyStatus: String | None
    CacheNodeIdsToReboot: CacheNodeIdsList | None


class CacheSecurityGroupMembership(TypedDict, total=False):
    CacheSecurityGroupName: String | None
    Status: String | None


CacheSecurityGroupMembershipList = list[CacheSecurityGroupMembership]


class NotificationConfiguration(TypedDict, total=False):
    TopicArn: String | None
    TopicStatus: String | None


class ScaleConfig(TypedDict, total=False):
    ScalePercentage: IntegerOptional | None
    ScaleIntervalMinutes: IntegerOptional | None


class PendingLogDeliveryConfiguration(TypedDict, total=False):
    LogType: LogType | None
    DestinationType: DestinationType | None
    DestinationDetails: DestinationDetails | None
    LogFormat: LogFormat | None


PendingLogDeliveryConfigurationList = list[PendingLogDeliveryConfiguration]


class PendingModifiedValues(TypedDict, total=False):
    NumCacheNodes: IntegerOptional | None
    CacheNodeIdsToRemove: CacheNodeIdsList | None
    EngineVersion: String | None
    CacheNodeType: String | None
    AuthTokenStatus: AuthTokenUpdateStatus | None
    LogDeliveryConfigurations: PendingLogDeliveryConfigurationList | None
    TransitEncryptionEnabled: BooleanOptional | None
    TransitEncryptionMode: TransitEncryptionMode | None
    ScaleConfig: ScaleConfig | None


class CacheCluster(TypedDict, total=False):
    CacheClusterId: String | None
    ConfigurationEndpoint: Endpoint | None
    ClientDownloadLandingPage: String | None
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    CacheClusterStatus: String | None
    NumCacheNodes: IntegerOptional | None
    PreferredAvailabilityZone: String | None
    PreferredOutpostArn: String | None
    CacheClusterCreateTime: TStamp | None
    PreferredMaintenanceWindow: String | None
    PendingModifiedValues: PendingModifiedValues | None
    NotificationConfiguration: NotificationConfiguration | None
    CacheSecurityGroups: CacheSecurityGroupMembershipList | None
    CacheParameterGroup: CacheParameterGroupStatus | None
    CacheSubnetGroupName: String | None
    CacheNodes: CacheNodeList | None
    AutoMinorVersionUpgrade: Boolean | None
    SecurityGroups: SecurityGroupMembershipList | None
    ReplicationGroupId: String | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    AuthTokenEnabled: BooleanOptional | None
    AuthTokenLastModifiedDate: TStamp | None
    TransitEncryptionEnabled: BooleanOptional | None
    AtRestEncryptionEnabled: BooleanOptional | None
    ARN: String | None
    ReplicationGroupLogDeliveryEnabled: Boolean | None
    LogDeliveryConfigurations: LogDeliveryConfigurationList | None
    NetworkType: NetworkType | None
    IpDiscovery: IpDiscovery | None
    TransitEncryptionMode: TransitEncryptionMode | None


CacheClusterList = list[CacheCluster]


class CacheClusterMessage(TypedDict, total=False):
    Marker: String | None
    CacheClusters: CacheClusterList | None


class CacheEngineVersion(TypedDict, total=False):
    Engine: String | None
    EngineVersion: String | None
    CacheParameterGroupFamily: String | None
    CacheEngineDescription: String | None
    CacheEngineVersionDescription: String | None


CacheEngineVersionList = list[CacheEngineVersion]


class CacheEngineVersionMessage(TypedDict, total=False):
    Marker: String | None
    CacheEngineVersions: CacheEngineVersionList | None


class CacheNodeTypeSpecificValue(TypedDict, total=False):
    CacheNodeType: String | None
    Value: String | None


CacheNodeTypeSpecificValueList = list[CacheNodeTypeSpecificValue]


class CacheNodeTypeSpecificParameter(TypedDict, total=False):
    ParameterName: String | None
    Description: String | None
    Source: String | None
    DataType: String | None
    AllowedValues: String | None
    IsModifiable: Boolean | None
    MinimumEngineVersion: String | None
    CacheNodeTypeSpecificValues: CacheNodeTypeSpecificValueList | None
    ChangeType: ChangeType | None


CacheNodeTypeSpecificParametersList = list[CacheNodeTypeSpecificParameter]


class CacheNodeUpdateStatus(TypedDict, total=False):
    CacheNodeId: String | None
    NodeUpdateStatus: NodeUpdateStatus | None
    NodeDeletionDate: TStamp | None
    NodeUpdateStartDate: TStamp | None
    NodeUpdateEndDate: TStamp | None
    NodeUpdateInitiatedBy: NodeUpdateInitiatedBy | None
    NodeUpdateInitiatedDate: TStamp | None
    NodeUpdateStatusModifiedDate: TStamp | None


CacheNodeUpdateStatusList = list[CacheNodeUpdateStatus]


class CacheParameterGroup(TypedDict, total=False):
    CacheParameterGroupName: String | None
    CacheParameterGroupFamily: String | None
    Description: String | None
    IsGlobal: Boolean | None
    ARN: String | None


class Parameter(TypedDict, total=False):
    ParameterName: String | None
    ParameterValue: String | None
    Description: String | None
    Source: String | None
    DataType: String | None
    AllowedValues: String | None
    IsModifiable: Boolean | None
    MinimumEngineVersion: String | None
    ChangeType: ChangeType | None


ParametersList = list[Parameter]


class CacheParameterGroupDetails(TypedDict, total=False):
    Marker: String | None
    Parameters: ParametersList | None
    CacheNodeTypeSpecificParameters: CacheNodeTypeSpecificParametersList | None


CacheParameterGroupList = list[CacheParameterGroup]


class CacheParameterGroupNameMessage(TypedDict, total=False):
    CacheParameterGroupName: String | None


class CacheParameterGroupsMessage(TypedDict, total=False):
    Marker: String | None
    CacheParameterGroups: CacheParameterGroupList | None


CacheSecurityGroups = list[CacheSecurityGroup]


class CacheSecurityGroupMessage(TypedDict, total=False):
    Marker: String | None
    CacheSecurityGroups: CacheSecurityGroups | None


CacheSecurityGroupNameList = list[String]
NetworkTypeList = list[NetworkType]


class SubnetOutpost(TypedDict, total=False):
    SubnetOutpostArn: String | None


class Subnet(TypedDict, total=False):
    SubnetIdentifier: String | None
    SubnetAvailabilityZone: AvailabilityZone | None
    SubnetOutpost: SubnetOutpost | None
    SupportedNetworkTypes: NetworkTypeList | None


SubnetList = list[Subnet]


class CacheSubnetGroup(TypedDict, total=False):
    CacheSubnetGroupName: String | None
    CacheSubnetGroupDescription: String | None
    VpcId: String | None
    Subnets: SubnetList | None
    ARN: String | None
    SupportedNetworkTypes: NetworkTypeList | None


CacheSubnetGroups = list[CacheSubnetGroup]


class CacheSubnetGroupMessage(TypedDict, total=False):
    Marker: String | None
    CacheSubnetGroups: CacheSubnetGroups | None


class ECPUPerSecond(TypedDict, total=False):
    Maximum: IntegerOptional | None
    Minimum: IntegerOptional | None


class DataStorage(TypedDict, total=False):
    Maximum: IntegerOptional | None
    Minimum: IntegerOptional | None
    Unit: DataStorageUnit


class CacheUsageLimits(TypedDict, total=False):
    DataStorage: DataStorage | None
    ECPUPerSecond: ECPUPerSecond | None


ClusterIdList = list[String]


class CompleteMigrationMessage(ServiceRequest):
    ReplicationGroupId: String
    Force: Boolean | None


UserGroupIdList = list[UserGroupId]
ReplicationGroupOutpostArnList = list[String]


class NodeGroupMember(TypedDict, total=False):
    CacheClusterId: String | None
    CacheNodeId: String | None
    ReadEndpoint: Endpoint | None
    PreferredAvailabilityZone: String | None
    PreferredOutpostArn: String | None
    CurrentRole: String | None


NodeGroupMemberList = list[NodeGroupMember]


class NodeGroup(TypedDict, total=False):
    NodeGroupId: String | None
    Status: String | None
    PrimaryEndpoint: Endpoint | None
    ReaderEndpoint: Endpoint | None
    Slots: String | None
    NodeGroupMembers: NodeGroupMemberList | None


NodeGroupList = list[NodeGroup]


class UserGroupsUpdateStatus(TypedDict, total=False):
    UserGroupIdsToAdd: UserGroupIdList | None
    UserGroupIdsToRemove: UserGroupIdList | None


class SlotMigration(TypedDict, total=False):
    ProgressPercentage: Double | None


class ReshardingStatus(TypedDict, total=False):
    SlotMigration: SlotMigration | None


class ReplicationGroupPendingModifiedValues(TypedDict, total=False):
    PrimaryClusterId: String | None
    AutomaticFailoverStatus: PendingAutomaticFailoverStatus | None
    Resharding: ReshardingStatus | None
    AuthTokenStatus: AuthTokenUpdateStatus | None
    UserGroups: UserGroupsUpdateStatus | None
    LogDeliveryConfigurations: PendingLogDeliveryConfigurationList | None
    TransitEncryptionEnabled: BooleanOptional | None
    TransitEncryptionMode: TransitEncryptionMode | None
    ClusterMode: ClusterMode | None


class GlobalReplicationGroupInfo(TypedDict, total=False):
    GlobalReplicationGroupId: String | None
    GlobalReplicationGroupMemberRole: String | None


class ReplicationGroup(TypedDict, total=False):
    ReplicationGroupId: String | None
    Description: String | None
    GlobalReplicationGroupInfo: GlobalReplicationGroupInfo | None
    Status: String | None
    PendingModifiedValues: ReplicationGroupPendingModifiedValues | None
    MemberClusters: ClusterIdList | None
    NodeGroups: NodeGroupList | None
    SnapshottingClusterId: String | None
    AutomaticFailover: AutomaticFailoverStatus | None
    MultiAZ: MultiAZStatus | None
    ConfigurationEndpoint: Endpoint | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    ClusterEnabled: BooleanOptional | None
    CacheNodeType: String | None
    AuthTokenEnabled: BooleanOptional | None
    AuthTokenLastModifiedDate: TStamp | None
    TransitEncryptionEnabled: BooleanOptional | None
    AtRestEncryptionEnabled: BooleanOptional | None
    MemberClustersOutpostArns: ReplicationGroupOutpostArnList | None
    KmsKeyId: String | None
    ARN: String | None
    UserGroupIds: UserGroupIdList | None
    LogDeliveryConfigurations: LogDeliveryConfigurationList | None
    ReplicationGroupCreateTime: TStamp | None
    DataTiering: DataTieringStatus | None
    AutoMinorVersionUpgrade: Boolean | None
    NetworkType: NetworkType | None
    IpDiscovery: IpDiscovery | None
    TransitEncryptionMode: TransitEncryptionMode | None
    ClusterMode: ClusterMode | None
    Engine: String | None


class CompleteMigrationResponse(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


PreferredOutpostArnList = list[String]
PreferredAvailabilityZoneList = list[String]


class ConfigureShard(TypedDict, total=False):
    NodeGroupId: AllowedNodeGroupId
    NewReplicaCount: Integer
    PreferredAvailabilityZones: PreferredAvailabilityZoneList | None
    PreferredOutpostArns: PreferredOutpostArnList | None


class CopyServerlessCacheSnapshotRequest(ServiceRequest):
    SourceServerlessCacheSnapshotName: String
    TargetServerlessCacheSnapshotName: String
    KmsKeyId: String | None
    Tags: TagList | None


class ServerlessCacheConfiguration(TypedDict, total=False):
    ServerlessCacheName: String | None
    Engine: String | None
    MajorEngineVersion: String | None


class ServerlessCacheSnapshot(TypedDict, total=False):
    ServerlessCacheSnapshotName: String | None
    ARN: String | None
    KmsKeyId: String | None
    SnapshotType: String | None
    Status: String | None
    CreateTime: TStamp | None
    ExpiryTime: TStamp | None
    BytesUsedForCache: String | None
    ServerlessCacheConfiguration: ServerlessCacheConfiguration | None


class CopyServerlessCacheSnapshotResponse(TypedDict, total=False):
    ServerlessCacheSnapshot: ServerlessCacheSnapshot | None


class CopySnapshotMessage(ServiceRequest):
    SourceSnapshotName: String
    TargetSnapshotName: String
    TargetBucket: String | None
    KmsKeyId: String | None
    Tags: TagList | None


OutpostArnsList = list[String]


class NodeGroupConfiguration(TypedDict, total=False):
    NodeGroupId: AllowedNodeGroupId | None
    Slots: String | None
    ReplicaCount: IntegerOptional | None
    PrimaryAvailabilityZone: String | None
    ReplicaAvailabilityZones: AvailabilityZonesList | None
    PrimaryOutpostArn: String | None
    ReplicaOutpostArns: OutpostArnsList | None


class NodeSnapshot(TypedDict, total=False):
    CacheClusterId: String | None
    NodeGroupId: String | None
    CacheNodeId: String | None
    NodeGroupConfiguration: NodeGroupConfiguration | None
    CacheSize: String | None
    CacheNodeCreateTime: TStamp | None
    SnapshotCreateTime: TStamp | None


NodeSnapshotList = list[NodeSnapshot]


class Snapshot(TypedDict, total=False):
    SnapshotName: String | None
    ReplicationGroupId: String | None
    ReplicationGroupDescription: String | None
    CacheClusterId: String | None
    SnapshotStatus: String | None
    SnapshotSource: String | None
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    NumCacheNodes: IntegerOptional | None
    PreferredAvailabilityZone: String | None
    PreferredOutpostArn: String | None
    CacheClusterCreateTime: TStamp | None
    PreferredMaintenanceWindow: String | None
    TopicArn: String | None
    Port: IntegerOptional | None
    CacheParameterGroupName: String | None
    CacheSubnetGroupName: String | None
    VpcId: String | None
    AutoMinorVersionUpgrade: Boolean | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    NumNodeGroups: IntegerOptional | None
    AutomaticFailover: AutomaticFailoverStatus | None
    NodeSnapshots: NodeSnapshotList | None
    KmsKeyId: String | None
    ARN: String | None
    DataTiering: DataTieringStatus | None


class CopySnapshotResult(TypedDict, total=False):
    Snapshot: Snapshot | None


class LogDeliveryConfigurationRequest(TypedDict, total=False):
    LogType: LogType | None
    DestinationType: DestinationType | None
    DestinationDetails: DestinationDetails | None
    LogFormat: LogFormat | None
    Enabled: BooleanOptional | None


LogDeliveryConfigurationRequestList = list[LogDeliveryConfigurationRequest]
SnapshotArnsList = list[String]
SecurityGroupIdsList = list[String]


class CreateCacheClusterMessage(ServiceRequest):
    CacheClusterId: String
    ReplicationGroupId: String | None
    AZMode: AZMode | None
    PreferredAvailabilityZone: String | None
    PreferredAvailabilityZones: PreferredAvailabilityZoneList | None
    NumCacheNodes: IntegerOptional | None
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    CacheParameterGroupName: String | None
    CacheSubnetGroupName: String | None
    CacheSecurityGroupNames: CacheSecurityGroupNameList | None
    SecurityGroupIds: SecurityGroupIdsList | None
    Tags: TagList | None
    SnapshotArns: SnapshotArnsList | None
    SnapshotName: String | None
    PreferredMaintenanceWindow: String | None
    Port: IntegerOptional | None
    NotificationTopicArn: String | None
    AutoMinorVersionUpgrade: BooleanOptional | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    AuthToken: String | None
    OutpostMode: OutpostMode | None
    PreferredOutpostArn: String | None
    PreferredOutpostArns: PreferredOutpostArnList | None
    LogDeliveryConfigurations: LogDeliveryConfigurationRequestList | None
    TransitEncryptionEnabled: BooleanOptional | None
    NetworkType: NetworkType | None
    IpDiscovery: IpDiscovery | None


class CreateCacheClusterResult(TypedDict, total=False):
    CacheCluster: CacheCluster | None


class CreateCacheParameterGroupMessage(ServiceRequest):
    CacheParameterGroupName: String
    CacheParameterGroupFamily: String
    Description: String
    Tags: TagList | None


class CreateCacheParameterGroupResult(TypedDict, total=False):
    CacheParameterGroup: CacheParameterGroup | None


class CreateCacheSecurityGroupMessage(ServiceRequest):
    CacheSecurityGroupName: String
    Description: String
    Tags: TagList | None


class CreateCacheSecurityGroupResult(TypedDict, total=False):
    CacheSecurityGroup: CacheSecurityGroup | None


SubnetIdentifierList = list[String]


class CreateCacheSubnetGroupMessage(ServiceRequest):
    CacheSubnetGroupName: String
    CacheSubnetGroupDescription: String
    SubnetIds: SubnetIdentifierList
    Tags: TagList | None


class CreateCacheSubnetGroupResult(TypedDict, total=False):
    CacheSubnetGroup: CacheSubnetGroup | None


class CreateGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupIdSuffix: String
    GlobalReplicationGroupDescription: String | None
    PrimaryReplicationGroupId: String


class GlobalNodeGroup(TypedDict, total=False):
    GlobalNodeGroupId: String | None
    Slots: String | None


GlobalNodeGroupList = list[GlobalNodeGroup]


class GlobalReplicationGroupMember(TypedDict, total=False):
    ReplicationGroupId: String | None
    ReplicationGroupRegion: String | None
    Role: String | None
    AutomaticFailover: AutomaticFailoverStatus | None
    Status: String | None


GlobalReplicationGroupMemberList = list[GlobalReplicationGroupMember]


class GlobalReplicationGroup(TypedDict, total=False):
    GlobalReplicationGroupId: String | None
    GlobalReplicationGroupDescription: String | None
    Status: String | None
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    Members: GlobalReplicationGroupMemberList | None
    ClusterEnabled: BooleanOptional | None
    GlobalNodeGroups: GlobalNodeGroupList | None
    AuthTokenEnabled: BooleanOptional | None
    TransitEncryptionEnabled: BooleanOptional | None
    AtRestEncryptionEnabled: BooleanOptional | None
    ARN: String | None


class CreateGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


UserGroupIdListInput = list[UserGroupId]
NodeGroupConfigurationList = list[NodeGroupConfiguration]


class CreateReplicationGroupMessage(ServiceRequest):
    ReplicationGroupId: String
    ReplicationGroupDescription: String
    GlobalReplicationGroupId: String | None
    PrimaryClusterId: String | None
    AutomaticFailoverEnabled: BooleanOptional | None
    MultiAZEnabled: BooleanOptional | None
    NumCacheClusters: IntegerOptional | None
    PreferredCacheClusterAZs: AvailabilityZonesList | None
    NumNodeGroups: IntegerOptional | None
    ReplicasPerNodeGroup: IntegerOptional | None
    NodeGroupConfiguration: NodeGroupConfigurationList | None
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    CacheParameterGroupName: String | None
    CacheSubnetGroupName: String | None
    CacheSecurityGroupNames: CacheSecurityGroupNameList | None
    SecurityGroupIds: SecurityGroupIdsList | None
    Tags: TagList | None
    SnapshotArns: SnapshotArnsList | None
    SnapshotName: String | None
    PreferredMaintenanceWindow: String | None
    Port: IntegerOptional | None
    NotificationTopicArn: String | None
    AutoMinorVersionUpgrade: BooleanOptional | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    AuthToken: String | None
    TransitEncryptionEnabled: BooleanOptional | None
    AtRestEncryptionEnabled: BooleanOptional | None
    KmsKeyId: String | None
    UserGroupIds: UserGroupIdListInput | None
    LogDeliveryConfigurations: LogDeliveryConfigurationRequestList | None
    DataTieringEnabled: BooleanOptional | None
    NetworkType: NetworkType | None
    IpDiscovery: IpDiscovery | None
    TransitEncryptionMode: TransitEncryptionMode | None
    ClusterMode: ClusterMode | None
    ServerlessCacheSnapshotName: String | None


class CreateReplicationGroupResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


SubnetIdsList = list[String]


class CreateServerlessCacheRequest(ServiceRequest):
    ServerlessCacheName: String
    Description: String | None
    Engine: String
    MajorEngineVersion: String | None
    CacheUsageLimits: CacheUsageLimits | None
    KmsKeyId: String | None
    SecurityGroupIds: SecurityGroupIdsList | None
    SnapshotArnsToRestore: SnapshotArnsList | None
    Tags: TagList | None
    UserGroupId: String | None
    SubnetIds: SubnetIdsList | None
    SnapshotRetentionLimit: IntegerOptional | None
    DailySnapshotTime: String | None


class ServerlessCache(TypedDict, total=False):
    ServerlessCacheName: String | None
    Description: String | None
    CreateTime: TStamp | None
    Status: String | None
    Engine: String | None
    MajorEngineVersion: String | None
    FullEngineVersion: String | None
    CacheUsageLimits: CacheUsageLimits | None
    KmsKeyId: String | None
    SecurityGroupIds: SecurityGroupIdsList | None
    Endpoint: Endpoint | None
    ReaderEndpoint: Endpoint | None
    ARN: String | None
    UserGroupId: String | None
    SubnetIds: SubnetIdsList | None
    SnapshotRetentionLimit: IntegerOptional | None
    DailySnapshotTime: String | None


class CreateServerlessCacheResponse(TypedDict, total=False):
    ServerlessCache: ServerlessCache | None


class CreateServerlessCacheSnapshotRequest(ServiceRequest):
    ServerlessCacheSnapshotName: String
    ServerlessCacheName: String
    KmsKeyId: String | None
    Tags: TagList | None


class CreateServerlessCacheSnapshotResponse(TypedDict, total=False):
    ServerlessCacheSnapshot: ServerlessCacheSnapshot | None


class CreateSnapshotMessage(ServiceRequest):
    ReplicationGroupId: String | None
    CacheClusterId: String | None
    SnapshotName: String
    KmsKeyId: String | None
    Tags: TagList | None


class CreateSnapshotResult(TypedDict, total=False):
    Snapshot: Snapshot | None


UserIdListInput = list[UserId]


class CreateUserGroupMessage(ServiceRequest):
    UserGroupId: String
    Engine: EngineType
    UserIds: UserIdListInput | None
    Tags: TagList | None


class CreateUserMessage(ServiceRequest):
    UserId: UserId
    UserName: UserName
    Engine: EngineType
    Passwords: PasswordListInput | None
    AccessString: AccessString
    NoPasswordRequired: BooleanOptional | None
    Tags: TagList | None
    AuthenticationMode: AuthenticationMode | None


class CustomerNodeEndpoint(TypedDict, total=False):
    Address: String | None
    Port: IntegerOptional | None


CustomerNodeEndpointList = list[CustomerNodeEndpoint]
GlobalNodeGroupIdList = list[String]


class DecreaseNodeGroupsInGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    NodeGroupCount: Integer
    GlobalNodeGroupsToRemove: GlobalNodeGroupIdList | None
    GlobalNodeGroupsToRetain: GlobalNodeGroupIdList | None
    ApplyImmediately: Boolean


class DecreaseNodeGroupsInGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


RemoveReplicasList = list[String]
ReplicaConfigurationList = list[ConfigureShard]


class DecreaseReplicaCountMessage(ServiceRequest):
    ReplicationGroupId: String
    NewReplicaCount: IntegerOptional | None
    ReplicaConfiguration: ReplicaConfigurationList | None
    ReplicasToRemove: RemoveReplicasList | None
    ApplyImmediately: Boolean


class DecreaseReplicaCountResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class DeleteCacheClusterMessage(ServiceRequest):
    CacheClusterId: String
    FinalSnapshotIdentifier: String | None


class DeleteCacheClusterResult(TypedDict, total=False):
    CacheCluster: CacheCluster | None


class DeleteCacheParameterGroupMessage(ServiceRequest):
    CacheParameterGroupName: String


class DeleteCacheSecurityGroupMessage(ServiceRequest):
    CacheSecurityGroupName: String


class DeleteCacheSubnetGroupMessage(ServiceRequest):
    CacheSubnetGroupName: String


class DeleteGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    RetainPrimaryReplicationGroup: Boolean


class DeleteGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class DeleteReplicationGroupMessage(ServiceRequest):
    ReplicationGroupId: String
    RetainPrimaryCluster: BooleanOptional | None
    FinalSnapshotIdentifier: String | None


class DeleteReplicationGroupResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class DeleteServerlessCacheRequest(ServiceRequest):
    ServerlessCacheName: String
    FinalSnapshotName: String | None


class DeleteServerlessCacheResponse(TypedDict, total=False):
    ServerlessCache: ServerlessCache | None


class DeleteServerlessCacheSnapshotRequest(ServiceRequest):
    ServerlessCacheSnapshotName: String


class DeleteServerlessCacheSnapshotResponse(TypedDict, total=False):
    ServerlessCacheSnapshot: ServerlessCacheSnapshot | None


class DeleteSnapshotMessage(ServiceRequest):
    SnapshotName: String


class DeleteSnapshotResult(TypedDict, total=False):
    Snapshot: Snapshot | None


class DeleteUserGroupMessage(ServiceRequest):
    UserGroupId: String


class DeleteUserMessage(ServiceRequest):
    UserId: UserId


class DescribeCacheClustersMessage(ServiceRequest):
    CacheClusterId: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None
    ShowCacheNodeInfo: BooleanOptional | None
    ShowCacheClustersNotInReplicationGroups: BooleanOptional | None


class DescribeCacheEngineVersionsMessage(ServiceRequest):
    Engine: String | None
    EngineVersion: String | None
    CacheParameterGroupFamily: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None
    DefaultOnly: Boolean | None


class DescribeCacheParameterGroupsMessage(ServiceRequest):
    CacheParameterGroupName: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeCacheParametersMessage(ServiceRequest):
    CacheParameterGroupName: String
    Source: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeCacheSecurityGroupsMessage(ServiceRequest):
    CacheSecurityGroupName: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeCacheSubnetGroupsMessage(ServiceRequest):
    CacheSubnetGroupName: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeEngineDefaultParametersMessage(ServiceRequest):
    CacheParameterGroupFamily: String
    MaxRecords: IntegerOptional | None
    Marker: String | None


class EngineDefaults(TypedDict, total=False):
    CacheParameterGroupFamily: String | None
    Marker: String | None
    Parameters: ParametersList | None
    CacheNodeTypeSpecificParameters: CacheNodeTypeSpecificParametersList | None


class DescribeEngineDefaultParametersResult(TypedDict, total=False):
    EngineDefaults: EngineDefaults | None


class DescribeEventsMessage(ServiceRequest):
    SourceIdentifier: String | None
    SourceType: SourceType | None
    StartTime: TStamp | None
    EndTime: TStamp | None
    Duration: IntegerOptional | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeGlobalReplicationGroupsMessage(ServiceRequest):
    GlobalReplicationGroupId: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None
    ShowMemberInfo: BooleanOptional | None


GlobalReplicationGroupList = list[GlobalReplicationGroup]


class DescribeGlobalReplicationGroupsResult(TypedDict, total=False):
    Marker: String | None
    GlobalReplicationGroups: GlobalReplicationGroupList | None


class DescribeReplicationGroupsMessage(ServiceRequest):
    ReplicationGroupId: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeReservedCacheNodesMessage(ServiceRequest):
    ReservedCacheNodeId: String | None
    ReservedCacheNodesOfferingId: String | None
    CacheNodeType: String | None
    Duration: String | None
    ProductDescription: String | None
    OfferingType: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeReservedCacheNodesOfferingsMessage(ServiceRequest):
    ReservedCacheNodesOfferingId: String | None
    CacheNodeType: String | None
    Duration: String | None
    ProductDescription: String | None
    OfferingType: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeServerlessCacheSnapshotsRequest(ServiceRequest):
    ServerlessCacheName: String | None
    ServerlessCacheSnapshotName: String | None
    SnapshotType: String | None
    NextToken: String | None
    MaxResults: IntegerOptional | None


ServerlessCacheSnapshotList = list[ServerlessCacheSnapshot]


class DescribeServerlessCacheSnapshotsResponse(TypedDict, total=False):
    NextToken: String | None
    ServerlessCacheSnapshots: ServerlessCacheSnapshotList | None


class DescribeServerlessCachesRequest(ServiceRequest):
    ServerlessCacheName: String | None
    MaxResults: IntegerOptional | None
    NextToken: String | None


ServerlessCacheList = list[ServerlessCache]


class DescribeServerlessCachesResponse(TypedDict, total=False):
    NextToken: String | None
    ServerlessCaches: ServerlessCacheList | None


ServiceUpdateStatusList = list[ServiceUpdateStatus]


class DescribeServiceUpdatesMessage(ServiceRequest):
    ServiceUpdateName: String | None
    ServiceUpdateStatus: ServiceUpdateStatusList | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


SnapshotList = list[Snapshot]


class DescribeSnapshotsListMessage(TypedDict, total=False):
    Marker: String | None
    Snapshots: SnapshotList | None


class DescribeSnapshotsMessage(ServiceRequest):
    ReplicationGroupId: String | None
    CacheClusterId: String | None
    SnapshotName: String | None
    SnapshotSource: String | None
    Marker: String | None
    MaxRecords: IntegerOptional | None
    ShowNodeGroupConfig: BooleanOptional | None


UpdateActionStatusList = list[UpdateActionStatus]


class TimeRangeFilter(TypedDict, total=False):
    StartTime: TStamp | None
    EndTime: TStamp | None


class DescribeUpdateActionsMessage(ServiceRequest):
    ServiceUpdateName: String | None
    ReplicationGroupIds: ReplicationGroupIdList | None
    CacheClusterIds: CacheClusterIdList | None
    Engine: String | None
    ServiceUpdateStatus: ServiceUpdateStatusList | None
    ServiceUpdateTimeRange: TimeRangeFilter | None
    UpdateActionStatus: UpdateActionStatusList | None
    ShowNodeLevelUpdateStatus: BooleanOptional | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class DescribeUserGroupsMessage(ServiceRequest):
    UserGroupId: String | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


UGServerlessCacheIdList = list[String]
UGReplicationGroupIdList = list[String]
UserIdList = list[UserId]


class UserGroupPendingChanges(TypedDict, total=False):
    UserIdsToRemove: UserIdList | None
    UserIdsToAdd: UserIdList | None


class UserGroup(TypedDict, total=False):
    UserGroupId: String | None
    Status: String | None
    Engine: EngineType | None
    UserIds: UserIdList | None
    MinimumEngineVersion: String | None
    PendingChanges: UserGroupPendingChanges | None
    ReplicationGroups: UGReplicationGroupIdList | None
    ServerlessCaches: UGServerlessCacheIdList | None
    ARN: String | None


UserGroupList = list[UserGroup]


class DescribeUserGroupsResult(TypedDict, total=False):
    UserGroups: UserGroupList | None
    Marker: String | None


FilterValueList = list[FilterValue]


class Filter(TypedDict, total=False):
    Name: FilterName
    Values: FilterValueList


FilterList = list[Filter]


class DescribeUsersMessage(ServiceRequest):
    Engine: EngineType | None
    UserId: UserId | None
    Filters: FilterList | None
    MaxRecords: IntegerOptional | None
    Marker: String | None


class User(TypedDict, total=False):
    UserId: String | None
    UserName: String | None
    Status: String | None
    Engine: EngineType | None
    MinimumEngineVersion: String | None
    AccessString: String | None
    UserGroupIds: UserGroupIdList | None
    Authentication: Authentication | None
    ARN: String | None


UserList = list[User]


class DescribeUsersResult(TypedDict, total=False):
    Users: UserList | None
    Marker: String | None


class DisassociateGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    ReplicationGroupId: String
    ReplicationGroupRegion: String


class DisassociateGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class Event(TypedDict, total=False):
    SourceIdentifier: String | None
    SourceType: SourceType | None
    Message: String | None
    Date: TStamp | None


EventList = list[Event]


class EventsMessage(TypedDict, total=False):
    Marker: String | None
    Events: EventList | None


class ExportServerlessCacheSnapshotRequest(ServiceRequest):
    ServerlessCacheSnapshotName: String
    S3BucketName: String


class ExportServerlessCacheSnapshotResponse(TypedDict, total=False):
    ServerlessCacheSnapshot: ServerlessCacheSnapshot | None


class FailoverGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    PrimaryRegion: String
    PrimaryReplicationGroupId: String


class FailoverGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class ReshardingConfiguration(TypedDict, total=False):
    NodeGroupId: AllowedNodeGroupId | None
    PreferredAvailabilityZones: AvailabilityZonesList | None


ReshardingConfigurationList = list[ReshardingConfiguration]


class RegionalConfiguration(TypedDict, total=False):
    ReplicationGroupId: String
    ReplicationGroupRegion: String
    ReshardingConfiguration: ReshardingConfigurationList


RegionalConfigurationList = list[RegionalConfiguration]


class IncreaseNodeGroupsInGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    NodeGroupCount: Integer
    RegionalConfigurations: RegionalConfigurationList | None
    ApplyImmediately: Boolean


class IncreaseNodeGroupsInGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class IncreaseReplicaCountMessage(ServiceRequest):
    ReplicationGroupId: String
    NewReplicaCount: IntegerOptional | None
    ReplicaConfiguration: ReplicaConfigurationList | None
    ApplyImmediately: Boolean


class IncreaseReplicaCountResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


KeyList = list[String]


class ListAllowedNodeTypeModificationsMessage(ServiceRequest):
    CacheClusterId: String | None
    ReplicationGroupId: String | None


class ListTagsForResourceMessage(ServiceRequest):
    ResourceName: String


class ModifyCacheClusterMessage(ServiceRequest):
    CacheClusterId: String
    NumCacheNodes: IntegerOptional | None
    CacheNodeIdsToRemove: CacheNodeIdsList | None
    AZMode: AZMode | None
    NewAvailabilityZones: PreferredAvailabilityZoneList | None
    CacheSecurityGroupNames: CacheSecurityGroupNameList | None
    SecurityGroupIds: SecurityGroupIdsList | None
    PreferredMaintenanceWindow: String | None
    NotificationTopicArn: String | None
    CacheParameterGroupName: String | None
    NotificationTopicStatus: String | None
    ApplyImmediately: Boolean | None
    Engine: String | None
    EngineVersion: String | None
    AutoMinorVersionUpgrade: BooleanOptional | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    CacheNodeType: String | None
    AuthToken: String | None
    AuthTokenUpdateStrategy: AuthTokenUpdateStrategyType | None
    LogDeliveryConfigurations: LogDeliveryConfigurationRequestList | None
    IpDiscovery: IpDiscovery | None
    ScaleConfig: ScaleConfig | None


class ModifyCacheClusterResult(TypedDict, total=False):
    CacheCluster: CacheCluster | None


class ParameterNameValue(TypedDict, total=False):
    ParameterName: String | None
    ParameterValue: String | None


ParameterNameValueList = list[ParameterNameValue]


class ModifyCacheParameterGroupMessage(ServiceRequest):
    CacheParameterGroupName: String
    ParameterNameValues: ParameterNameValueList


class ModifyCacheSubnetGroupMessage(ServiceRequest):
    CacheSubnetGroupName: String
    CacheSubnetGroupDescription: String | None
    SubnetIds: SubnetIdentifierList | None


class ModifyCacheSubnetGroupResult(TypedDict, total=False):
    CacheSubnetGroup: CacheSubnetGroup | None


class ModifyGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    ApplyImmediately: Boolean
    CacheNodeType: String | None
    Engine: String | None
    EngineVersion: String | None
    CacheParameterGroupName: String | None
    GlobalReplicationGroupDescription: String | None
    AutomaticFailoverEnabled: BooleanOptional | None


class ModifyGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class ModifyReplicationGroupMessage(ServiceRequest):
    ReplicationGroupId: String
    ReplicationGroupDescription: String | None
    PrimaryClusterId: String | None
    SnapshottingClusterId: String | None
    AutomaticFailoverEnabled: BooleanOptional | None
    MultiAZEnabled: BooleanOptional | None
    NodeGroupId: String | None
    CacheSecurityGroupNames: CacheSecurityGroupNameList | None
    SecurityGroupIds: SecurityGroupIdsList | None
    PreferredMaintenanceWindow: String | None
    NotificationTopicArn: String | None
    CacheParameterGroupName: String | None
    NotificationTopicStatus: String | None
    ApplyImmediately: Boolean | None
    Engine: String | None
    EngineVersion: String | None
    AutoMinorVersionUpgrade: BooleanOptional | None
    SnapshotRetentionLimit: IntegerOptional | None
    SnapshotWindow: String | None
    CacheNodeType: String | None
    AuthToken: String | None
    AuthTokenUpdateStrategy: AuthTokenUpdateStrategyType | None
    UserGroupIdsToAdd: UserGroupIdList | None
    UserGroupIdsToRemove: UserGroupIdList | None
    RemoveUserGroups: BooleanOptional | None
    LogDeliveryConfigurations: LogDeliveryConfigurationRequestList | None
    IpDiscovery: IpDiscovery | None
    TransitEncryptionEnabled: BooleanOptional | None
    TransitEncryptionMode: TransitEncryptionMode | None
    ClusterMode: ClusterMode | None


class ModifyReplicationGroupResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


NodeGroupsToRetainList = list[AllowedNodeGroupId]
NodeGroupsToRemoveList = list[AllowedNodeGroupId]


class ModifyReplicationGroupShardConfigurationMessage(ServiceRequest):
    ReplicationGroupId: String
    NodeGroupCount: Integer
    ApplyImmediately: Boolean
    ReshardingConfiguration: ReshardingConfigurationList | None
    NodeGroupsToRemove: NodeGroupsToRemoveList | None
    NodeGroupsToRetain: NodeGroupsToRetainList | None


class ModifyReplicationGroupShardConfigurationResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class ModifyServerlessCacheRequest(ServiceRequest):
    ServerlessCacheName: String
    Description: String | None
    CacheUsageLimits: CacheUsageLimits | None
    RemoveUserGroup: BooleanOptional | None
    UserGroupId: String | None
    SecurityGroupIds: SecurityGroupIdsList | None
    SnapshotRetentionLimit: IntegerOptional | None
    DailySnapshotTime: String | None
    Engine: String | None
    MajorEngineVersion: String | None


class ModifyServerlessCacheResponse(TypedDict, total=False):
    ServerlessCache: ServerlessCache | None


class ModifyUserGroupMessage(ServiceRequest):
    UserGroupId: String
    UserIdsToAdd: UserIdListInput | None
    UserIdsToRemove: UserIdListInput | None
    Engine: EngineType | None


class ModifyUserMessage(ServiceRequest):
    UserId: UserId
    AccessString: AccessString | None
    AppendAccessString: AccessString | None
    Passwords: PasswordListInput | None
    NoPasswordRequired: BooleanOptional | None
    AuthenticationMode: AuthenticationMode | None
    Engine: EngineType | None


class NodeGroupMemberUpdateStatus(TypedDict, total=False):
    CacheClusterId: String | None
    CacheNodeId: String | None
    NodeUpdateStatus: NodeUpdateStatus | None
    NodeDeletionDate: TStamp | None
    NodeUpdateStartDate: TStamp | None
    NodeUpdateEndDate: TStamp | None
    NodeUpdateInitiatedBy: NodeUpdateInitiatedBy | None
    NodeUpdateInitiatedDate: TStamp | None
    NodeUpdateStatusModifiedDate: TStamp | None


NodeGroupMemberUpdateStatusList = list[NodeGroupMemberUpdateStatus]


class NodeGroupUpdateStatus(TypedDict, total=False):
    NodeGroupId: String | None
    NodeGroupMemberUpdateStatus: NodeGroupMemberUpdateStatusList | None


NodeGroupUpdateStatusList = list[NodeGroupUpdateStatus]


class ProcessedUpdateAction(TypedDict, total=False):
    ReplicationGroupId: String | None
    CacheClusterId: String | None
    ServiceUpdateName: String | None
    UpdateActionStatus: UpdateActionStatus | None


ProcessedUpdateActionList = list[ProcessedUpdateAction]


class PurchaseReservedCacheNodesOfferingMessage(ServiceRequest):
    ReservedCacheNodesOfferingId: String
    ReservedCacheNodeId: String | None
    CacheNodeCount: IntegerOptional | None
    Tags: TagList | None


class RecurringCharge(TypedDict, total=False):
    RecurringChargeAmount: Double | None
    RecurringChargeFrequency: String | None


RecurringChargeList = list[RecurringCharge]


class ReservedCacheNode(TypedDict, total=False):
    ReservedCacheNodeId: String | None
    ReservedCacheNodesOfferingId: String | None
    CacheNodeType: String | None
    StartTime: TStamp | None
    Duration: Integer | None
    FixedPrice: Double | None
    UsagePrice: Double | None
    CacheNodeCount: Integer | None
    ProductDescription: String | None
    OfferingType: String | None
    State: String | None
    RecurringCharges: RecurringChargeList | None
    ReservationARN: String | None


class PurchaseReservedCacheNodesOfferingResult(TypedDict, total=False):
    ReservedCacheNode: ReservedCacheNode | None


class RebalanceSlotsInGlobalReplicationGroupMessage(ServiceRequest):
    GlobalReplicationGroupId: String
    ApplyImmediately: Boolean


class RebalanceSlotsInGlobalReplicationGroupResult(TypedDict, total=False):
    GlobalReplicationGroup: GlobalReplicationGroup | None


class RebootCacheClusterMessage(ServiceRequest):
    CacheClusterId: String
    CacheNodeIdsToReboot: CacheNodeIdsList


class RebootCacheClusterResult(TypedDict, total=False):
    CacheCluster: CacheCluster | None


class RemoveTagsFromResourceMessage(ServiceRequest):
    ResourceName: String
    TagKeys: KeyList


ReplicationGroupList = list[ReplicationGroup]


class ReplicationGroupMessage(TypedDict, total=False):
    Marker: String | None
    ReplicationGroups: ReplicationGroupList | None


ReservedCacheNodeList = list[ReservedCacheNode]


class ReservedCacheNodeMessage(TypedDict, total=False):
    Marker: String | None
    ReservedCacheNodes: ReservedCacheNodeList | None


class ReservedCacheNodesOffering(TypedDict, total=False):
    ReservedCacheNodesOfferingId: String | None
    CacheNodeType: String | None
    Duration: Integer | None
    FixedPrice: Double | None
    UsagePrice: Double | None
    ProductDescription: String | None
    OfferingType: String | None
    RecurringCharges: RecurringChargeList | None


ReservedCacheNodesOfferingList = list[ReservedCacheNodesOffering]


class ReservedCacheNodesOfferingMessage(TypedDict, total=False):
    Marker: String | None
    ReservedCacheNodesOfferings: ReservedCacheNodesOfferingList | None


class ResetCacheParameterGroupMessage(ServiceRequest):
    CacheParameterGroupName: String
    ResetAllParameters: Boolean | None
    ParameterNameValues: ParameterNameValueList | None


class RevokeCacheSecurityGroupIngressMessage(ServiceRequest):
    CacheSecurityGroupName: String
    EC2SecurityGroupName: String
    EC2SecurityGroupOwnerId: String


class RevokeCacheSecurityGroupIngressResult(TypedDict, total=False):
    CacheSecurityGroup: CacheSecurityGroup | None


class ServiceUpdate(TypedDict, total=False):
    ServiceUpdateName: String | None
    ServiceUpdateReleaseDate: TStamp | None
    ServiceUpdateEndDate: TStamp | None
    ServiceUpdateSeverity: ServiceUpdateSeverity | None
    ServiceUpdateRecommendedApplyByDate: TStamp | None
    ServiceUpdateStatus: ServiceUpdateStatus | None
    ServiceUpdateDescription: String | None
    ServiceUpdateType: ServiceUpdateType | None
    Engine: String | None
    EngineVersion: String | None
    AutoUpdateAfterRecommendedApplyByDate: BooleanOptional | None
    EstimatedUpdateTime: String | None


ServiceUpdateList = list[ServiceUpdate]


class ServiceUpdatesMessage(TypedDict, total=False):
    Marker: String | None
    ServiceUpdates: ServiceUpdateList | None


class StartMigrationMessage(ServiceRequest):
    ReplicationGroupId: String
    CustomerNodeEndpointList: CustomerNodeEndpointList


class StartMigrationResponse(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class TagListMessage(TypedDict, total=False):
    TagList: TagList | None


class TestFailoverMessage(ServiceRequest):
    ReplicationGroupId: String
    NodeGroupId: AllowedNodeGroupId


class TestFailoverResult(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class TestMigrationMessage(ServiceRequest):
    ReplicationGroupId: String
    CustomerNodeEndpointList: CustomerNodeEndpointList


class TestMigrationResponse(TypedDict, total=False):
    ReplicationGroup: ReplicationGroup | None


class UnprocessedUpdateAction(TypedDict, total=False):
    ReplicationGroupId: String | None
    CacheClusterId: String | None
    ServiceUpdateName: String | None
    ErrorType: String | None
    ErrorMessage: String | None


UnprocessedUpdateActionList = list[UnprocessedUpdateAction]


class UpdateAction(TypedDict, total=False):
    ReplicationGroupId: String | None
    CacheClusterId: String | None
    ServiceUpdateName: String | None
    ServiceUpdateReleaseDate: TStamp | None
    ServiceUpdateSeverity: ServiceUpdateSeverity | None
    ServiceUpdateStatus: ServiceUpdateStatus | None
    ServiceUpdateRecommendedApplyByDate: TStamp | None
    ServiceUpdateType: ServiceUpdateType | None
    UpdateActionAvailableDate: TStamp | None
    UpdateActionStatus: UpdateActionStatus | None
    NodesUpdated: String | None
    UpdateActionStatusModifiedDate: TStamp | None
    SlaMet: SlaMet | None
    NodeGroupUpdateStatus: NodeGroupUpdateStatusList | None
    CacheNodeUpdateStatus: CacheNodeUpdateStatusList | None
    EstimatedUpdateTime: String | None
    Engine: String | None


UpdateActionList = list[UpdateAction]


class UpdateActionResultsMessage(TypedDict, total=False):
    ProcessedUpdateActions: ProcessedUpdateActionList | None
    UnprocessedUpdateActions: UnprocessedUpdateActionList | None


class UpdateActionsMessage(TypedDict, total=False):
    Marker: String | None
    UpdateActions: UpdateActionList | None


class ElasticacheApi:
    service: str = "elasticache"
    version: str = "2015-02-02"

    @handler("AddTagsToResource")
    def add_tags_to_resource(
        self, context: RequestContext, resource_name: String, tags: TagList, **kwargs
    ) -> TagListMessage:
        raise NotImplementedError

    @handler("AuthorizeCacheSecurityGroupIngress")
    def authorize_cache_security_group_ingress(
        self,
        context: RequestContext,
        cache_security_group_name: String,
        ec2_security_group_name: String,
        ec2_security_group_owner_id: String,
        **kwargs,
    ) -> AuthorizeCacheSecurityGroupIngressResult:
        raise NotImplementedError

    @handler("BatchApplyUpdateAction")
    def batch_apply_update_action(
        self,
        context: RequestContext,
        service_update_name: String,
        replication_group_ids: ReplicationGroupIdList | None = None,
        cache_cluster_ids: CacheClusterIdList | None = None,
        **kwargs,
    ) -> UpdateActionResultsMessage:
        raise NotImplementedError

    @handler("BatchStopUpdateAction")
    def batch_stop_update_action(
        self,
        context: RequestContext,
        service_update_name: String,
        replication_group_ids: ReplicationGroupIdList | None = None,
        cache_cluster_ids: CacheClusterIdList | None = None,
        **kwargs,
    ) -> UpdateActionResultsMessage:
        raise NotImplementedError

    @handler("CompleteMigration")
    def complete_migration(
        self,
        context: RequestContext,
        replication_group_id: String,
        force: Boolean | None = None,
        **kwargs,
    ) -> CompleteMigrationResponse:
        raise NotImplementedError

    @handler("CopyServerlessCacheSnapshot")
    def copy_serverless_cache_snapshot(
        self,
        context: RequestContext,
        source_serverless_cache_snapshot_name: String,
        target_serverless_cache_snapshot_name: String,
        kms_key_id: String | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> CopyServerlessCacheSnapshotResponse:
        raise NotImplementedError

    @handler("CopySnapshot")
    def copy_snapshot(
        self,
        context: RequestContext,
        source_snapshot_name: String,
        target_snapshot_name: String,
        target_bucket: String | None = None,
        kms_key_id: String | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> CopySnapshotResult:
        raise NotImplementedError

    @handler("CreateCacheCluster")
    def create_cache_cluster(
        self,
        context: RequestContext,
        cache_cluster_id: String,
        replication_group_id: String | None = None,
        az_mode: AZMode | None = None,
        preferred_availability_zone: String | None = None,
        preferred_availability_zones: PreferredAvailabilityZoneList | None = None,
        num_cache_nodes: IntegerOptional | None = None,
        cache_node_type: String | None = None,
        engine: String | None = None,
        engine_version: String | None = None,
        cache_parameter_group_name: String | None = None,
        cache_subnet_group_name: String | None = None,
        cache_security_group_names: CacheSecurityGroupNameList | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        tags: TagList | None = None,
        snapshot_arns: SnapshotArnsList | None = None,
        snapshot_name: String | None = None,
        preferred_maintenance_window: String | None = None,
        port: IntegerOptional | None = None,
        notification_topic_arn: String | None = None,
        auto_minor_version_upgrade: BooleanOptional | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        snapshot_window: String | None = None,
        auth_token: String | None = None,
        outpost_mode: OutpostMode | None = None,
        preferred_outpost_arn: String | None = None,
        preferred_outpost_arns: PreferredOutpostArnList | None = None,
        log_delivery_configurations: LogDeliveryConfigurationRequestList | None = None,
        transit_encryption_enabled: BooleanOptional | None = None,
        network_type: NetworkType | None = None,
        ip_discovery: IpDiscovery | None = None,
        **kwargs,
    ) -> CreateCacheClusterResult:
        raise NotImplementedError

    @handler("CreateCacheParameterGroup")
    def create_cache_parameter_group(
        self,
        context: RequestContext,
        cache_parameter_group_name: String,
        cache_parameter_group_family: String,
        description: String,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateCacheParameterGroupResult:
        raise NotImplementedError

    @handler("CreateCacheSecurityGroup")
    def create_cache_security_group(
        self,
        context: RequestContext,
        cache_security_group_name: String,
        description: String,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateCacheSecurityGroupResult:
        raise NotImplementedError

    @handler("CreateCacheSubnetGroup")
    def create_cache_subnet_group(
        self,
        context: RequestContext,
        cache_subnet_group_name: String,
        cache_subnet_group_description: String,
        subnet_ids: SubnetIdentifierList,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateCacheSubnetGroupResult:
        raise NotImplementedError

    @handler("CreateGlobalReplicationGroup")
    def create_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id_suffix: String,
        primary_replication_group_id: String,
        global_replication_group_description: String | None = None,
        **kwargs,
    ) -> CreateGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("CreateReplicationGroup")
    def create_replication_group(
        self,
        context: RequestContext,
        replication_group_id: String,
        replication_group_description: String,
        global_replication_group_id: String | None = None,
        primary_cluster_id: String | None = None,
        automatic_failover_enabled: BooleanOptional | None = None,
        multi_az_enabled: BooleanOptional | None = None,
        num_cache_clusters: IntegerOptional | None = None,
        preferred_cache_cluster_azs: AvailabilityZonesList | None = None,
        num_node_groups: IntegerOptional | None = None,
        replicas_per_node_group: IntegerOptional | None = None,
        node_group_configuration: NodeGroupConfigurationList | None = None,
        cache_node_type: String | None = None,
        engine: String | None = None,
        engine_version: String | None = None,
        cache_parameter_group_name: String | None = None,
        cache_subnet_group_name: String | None = None,
        cache_security_group_names: CacheSecurityGroupNameList | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        tags: TagList | None = None,
        snapshot_arns: SnapshotArnsList | None = None,
        snapshot_name: String | None = None,
        preferred_maintenance_window: String | None = None,
        port: IntegerOptional | None = None,
        notification_topic_arn: String | None = None,
        auto_minor_version_upgrade: BooleanOptional | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        snapshot_window: String | None = None,
        auth_token: String | None = None,
        transit_encryption_enabled: BooleanOptional | None = None,
        at_rest_encryption_enabled: BooleanOptional | None = None,
        kms_key_id: String | None = None,
        user_group_ids: UserGroupIdListInput | None = None,
        log_delivery_configurations: LogDeliveryConfigurationRequestList | None = None,
        data_tiering_enabled: BooleanOptional | None = None,
        network_type: NetworkType | None = None,
        ip_discovery: IpDiscovery | None = None,
        transit_encryption_mode: TransitEncryptionMode | None = None,
        cluster_mode: ClusterMode | None = None,
        serverless_cache_snapshot_name: String | None = None,
        **kwargs,
    ) -> CreateReplicationGroupResult:
        raise NotImplementedError

    @handler("CreateServerlessCache")
    def create_serverless_cache(
        self,
        context: RequestContext,
        serverless_cache_name: String,
        engine: String,
        description: String | None = None,
        major_engine_version: String | None = None,
        cache_usage_limits: CacheUsageLimits | None = None,
        kms_key_id: String | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        snapshot_arns_to_restore: SnapshotArnsList | None = None,
        tags: TagList | None = None,
        user_group_id: String | None = None,
        subnet_ids: SubnetIdsList | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        daily_snapshot_time: String | None = None,
        **kwargs,
    ) -> CreateServerlessCacheResponse:
        raise NotImplementedError

    @handler("CreateServerlessCacheSnapshot")
    def create_serverless_cache_snapshot(
        self,
        context: RequestContext,
        serverless_cache_snapshot_name: String,
        serverless_cache_name: String,
        kms_key_id: String | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateServerlessCacheSnapshotResponse:
        raise NotImplementedError

    @handler("CreateSnapshot")
    def create_snapshot(
        self,
        context: RequestContext,
        snapshot_name: String,
        replication_group_id: String | None = None,
        cache_cluster_id: String | None = None,
        kms_key_id: String | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateSnapshotResult:
        raise NotImplementedError

    @handler("CreateUser")
    def create_user(
        self,
        context: RequestContext,
        user_id: UserId,
        user_name: UserName,
        engine: EngineType,
        access_string: AccessString,
        passwords: PasswordListInput | None = None,
        no_password_required: BooleanOptional | None = None,
        tags: TagList | None = None,
        authentication_mode: AuthenticationMode | None = None,
        **kwargs,
    ) -> User:
        raise NotImplementedError

    @handler("CreateUserGroup")
    def create_user_group(
        self,
        context: RequestContext,
        user_group_id: String,
        engine: EngineType,
        user_ids: UserIdListInput | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> UserGroup:
        raise NotImplementedError

    @handler("DecreaseNodeGroupsInGlobalReplicationGroup")
    def decrease_node_groups_in_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        node_group_count: Integer,
        apply_immediately: Boolean,
        global_node_groups_to_remove: GlobalNodeGroupIdList | None = None,
        global_node_groups_to_retain: GlobalNodeGroupIdList | None = None,
        **kwargs,
    ) -> DecreaseNodeGroupsInGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("DecreaseReplicaCount")
    def decrease_replica_count(
        self,
        context: RequestContext,
        replication_group_id: String,
        apply_immediately: Boolean,
        new_replica_count: IntegerOptional | None = None,
        replica_configuration: ReplicaConfigurationList | None = None,
        replicas_to_remove: RemoveReplicasList | None = None,
        **kwargs,
    ) -> DecreaseReplicaCountResult:
        raise NotImplementedError

    @handler("DeleteCacheCluster")
    def delete_cache_cluster(
        self,
        context: RequestContext,
        cache_cluster_id: String,
        final_snapshot_identifier: String | None = None,
        **kwargs,
    ) -> DeleteCacheClusterResult:
        raise NotImplementedError

    @handler("DeleteCacheParameterGroup")
    def delete_cache_parameter_group(
        self, context: RequestContext, cache_parameter_group_name: String, **kwargs
    ) -> None:
        raise NotImplementedError

    @handler("DeleteCacheSecurityGroup")
    def delete_cache_security_group(
        self, context: RequestContext, cache_security_group_name: String, **kwargs
    ) -> None:
        raise NotImplementedError

    @handler("DeleteCacheSubnetGroup")
    def delete_cache_subnet_group(
        self, context: RequestContext, cache_subnet_group_name: String, **kwargs
    ) -> None:
        raise NotImplementedError

    @handler("DeleteGlobalReplicationGroup")
    def delete_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        retain_primary_replication_group: Boolean,
        **kwargs,
    ) -> DeleteGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("DeleteReplicationGroup")
    def delete_replication_group(
        self,
        context: RequestContext,
        replication_group_id: String,
        retain_primary_cluster: BooleanOptional | None = None,
        final_snapshot_identifier: String | None = None,
        **kwargs,
    ) -> DeleteReplicationGroupResult:
        raise NotImplementedError

    @handler("DeleteServerlessCache")
    def delete_serverless_cache(
        self,
        context: RequestContext,
        serverless_cache_name: String,
        final_snapshot_name: String | None = None,
        **kwargs,
    ) -> DeleteServerlessCacheResponse:
        raise NotImplementedError

    @handler("DeleteServerlessCacheSnapshot")
    def delete_serverless_cache_snapshot(
        self, context: RequestContext, serverless_cache_snapshot_name: String, **kwargs
    ) -> DeleteServerlessCacheSnapshotResponse:
        raise NotImplementedError

    @handler("DeleteSnapshot")
    def delete_snapshot(
        self, context: RequestContext, snapshot_name: String, **kwargs
    ) -> DeleteSnapshotResult:
        raise NotImplementedError

    @handler("DeleteUser")
    def delete_user(self, context: RequestContext, user_id: UserId, **kwargs) -> User:
        raise NotImplementedError

    @handler("DeleteUserGroup")
    def delete_user_group(
        self, context: RequestContext, user_group_id: String, **kwargs
    ) -> UserGroup:
        raise NotImplementedError

    @handler("DescribeCacheClusters")
    def describe_cache_clusters(
        self,
        context: RequestContext,
        cache_cluster_id: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        show_cache_node_info: BooleanOptional | None = None,
        show_cache_clusters_not_in_replication_groups: BooleanOptional | None = None,
        **kwargs,
    ) -> CacheClusterMessage:
        raise NotImplementedError

    @handler("DescribeCacheEngineVersions")
    def describe_cache_engine_versions(
        self,
        context: RequestContext,
        engine: String | None = None,
        engine_version: String | None = None,
        cache_parameter_group_family: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        default_only: Boolean | None = None,
        **kwargs,
    ) -> CacheEngineVersionMessage:
        raise NotImplementedError

    @handler("DescribeCacheParameterGroups")
    def describe_cache_parameter_groups(
        self,
        context: RequestContext,
        cache_parameter_group_name: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> CacheParameterGroupsMessage:
        raise NotImplementedError

    @handler("DescribeCacheParameters")
    def describe_cache_parameters(
        self,
        context: RequestContext,
        cache_parameter_group_name: String,
        source: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> CacheParameterGroupDetails:
        raise NotImplementedError

    @handler("DescribeCacheSecurityGroups")
    def describe_cache_security_groups(
        self,
        context: RequestContext,
        cache_security_group_name: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> CacheSecurityGroupMessage:
        raise NotImplementedError

    @handler("DescribeCacheSubnetGroups")
    def describe_cache_subnet_groups(
        self,
        context: RequestContext,
        cache_subnet_group_name: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> CacheSubnetGroupMessage:
        raise NotImplementedError

    @handler("DescribeEngineDefaultParameters")
    def describe_engine_default_parameters(
        self,
        context: RequestContext,
        cache_parameter_group_family: String,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> DescribeEngineDefaultParametersResult:
        raise NotImplementedError

    @handler("DescribeEvents")
    def describe_events(
        self,
        context: RequestContext,
        source_identifier: String | None = None,
        source_type: SourceType | None = None,
        start_time: TStamp | None = None,
        end_time: TStamp | None = None,
        duration: IntegerOptional | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> EventsMessage:
        raise NotImplementedError

    @handler("DescribeGlobalReplicationGroups")
    def describe_global_replication_groups(
        self,
        context: RequestContext,
        global_replication_group_id: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        show_member_info: BooleanOptional | None = None,
        **kwargs,
    ) -> DescribeGlobalReplicationGroupsResult:
        raise NotImplementedError

    @handler("DescribeReplicationGroups")
    def describe_replication_groups(
        self,
        context: RequestContext,
        replication_group_id: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> ReplicationGroupMessage:
        raise NotImplementedError

    @handler("DescribeReservedCacheNodes")
    def describe_reserved_cache_nodes(
        self,
        context: RequestContext,
        reserved_cache_node_id: String | None = None,
        reserved_cache_nodes_offering_id: String | None = None,
        cache_node_type: String | None = None,
        duration: String | None = None,
        product_description: String | None = None,
        offering_type: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> ReservedCacheNodeMessage:
        raise NotImplementedError

    @handler("DescribeReservedCacheNodesOfferings")
    def describe_reserved_cache_nodes_offerings(
        self,
        context: RequestContext,
        reserved_cache_nodes_offering_id: String | None = None,
        cache_node_type: String | None = None,
        duration: String | None = None,
        product_description: String | None = None,
        offering_type: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> ReservedCacheNodesOfferingMessage:
        raise NotImplementedError

    @handler("DescribeServerlessCacheSnapshots")
    def describe_serverless_cache_snapshots(
        self,
        context: RequestContext,
        serverless_cache_name: String | None = None,
        serverless_cache_snapshot_name: String | None = None,
        snapshot_type: String | None = None,
        next_token: String | None = None,
        max_results: IntegerOptional | None = None,
        **kwargs,
    ) -> DescribeServerlessCacheSnapshotsResponse:
        raise NotImplementedError

    @handler("DescribeServerlessCaches")
    def describe_serverless_caches(
        self,
        context: RequestContext,
        serverless_cache_name: String | None = None,
        max_results: IntegerOptional | None = None,
        next_token: String | None = None,
        **kwargs,
    ) -> DescribeServerlessCachesResponse:
        raise NotImplementedError

    @handler("DescribeServiceUpdates")
    def describe_service_updates(
        self,
        context: RequestContext,
        service_update_name: String | None = None,
        service_update_status: ServiceUpdateStatusList | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> ServiceUpdatesMessage:
        raise NotImplementedError

    @handler("DescribeSnapshots")
    def describe_snapshots(
        self,
        context: RequestContext,
        replication_group_id: String | None = None,
        cache_cluster_id: String | None = None,
        snapshot_name: String | None = None,
        snapshot_source: String | None = None,
        marker: String | None = None,
        max_records: IntegerOptional | None = None,
        show_node_group_config: BooleanOptional | None = None,
        **kwargs,
    ) -> DescribeSnapshotsListMessage:
        raise NotImplementedError

    @handler("DescribeUpdateActions")
    def describe_update_actions(
        self,
        context: RequestContext,
        service_update_name: String | None = None,
        replication_group_ids: ReplicationGroupIdList | None = None,
        cache_cluster_ids: CacheClusterIdList | None = None,
        engine: String | None = None,
        service_update_status: ServiceUpdateStatusList | None = None,
        service_update_time_range: TimeRangeFilter | None = None,
        update_action_status: UpdateActionStatusList | None = None,
        show_node_level_update_status: BooleanOptional | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> UpdateActionsMessage:
        raise NotImplementedError

    @handler("DescribeUserGroups")
    def describe_user_groups(
        self,
        context: RequestContext,
        user_group_id: String | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> DescribeUserGroupsResult:
        raise NotImplementedError

    @handler("DescribeUsers")
    def describe_users(
        self,
        context: RequestContext,
        engine: EngineType | None = None,
        user_id: UserId | None = None,
        filters: FilterList | None = None,
        max_records: IntegerOptional | None = None,
        marker: String | None = None,
        **kwargs,
    ) -> DescribeUsersResult:
        raise NotImplementedError

    @handler("DisassociateGlobalReplicationGroup")
    def disassociate_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        replication_group_id: String,
        replication_group_region: String,
        **kwargs,
    ) -> DisassociateGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("ExportServerlessCacheSnapshot")
    def export_serverless_cache_snapshot(
        self,
        context: RequestContext,
        serverless_cache_snapshot_name: String,
        s3_bucket_name: String,
        **kwargs,
    ) -> ExportServerlessCacheSnapshotResponse:
        raise NotImplementedError

    @handler("FailoverGlobalReplicationGroup")
    def failover_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        primary_region: String,
        primary_replication_group_id: String,
        **kwargs,
    ) -> FailoverGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("IncreaseNodeGroupsInGlobalReplicationGroup")
    def increase_node_groups_in_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        node_group_count: Integer,
        apply_immediately: Boolean,
        regional_configurations: RegionalConfigurationList | None = None,
        **kwargs,
    ) -> IncreaseNodeGroupsInGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("IncreaseReplicaCount")
    def increase_replica_count(
        self,
        context: RequestContext,
        replication_group_id: String,
        apply_immediately: Boolean,
        new_replica_count: IntegerOptional | None = None,
        replica_configuration: ReplicaConfigurationList | None = None,
        **kwargs,
    ) -> IncreaseReplicaCountResult:
        raise NotImplementedError

    @handler("ListAllowedNodeTypeModifications")
    def list_allowed_node_type_modifications(
        self,
        context: RequestContext,
        cache_cluster_id: String | None = None,
        replication_group_id: String | None = None,
        **kwargs,
    ) -> AllowedNodeTypeModificationsMessage:
        raise NotImplementedError

    @handler("ListTagsForResource")
    def list_tags_for_resource(
        self, context: RequestContext, resource_name: String, **kwargs
    ) -> TagListMessage:
        raise NotImplementedError

    @handler("ModifyCacheCluster")
    def modify_cache_cluster(
        self,
        context: RequestContext,
        cache_cluster_id: String,
        num_cache_nodes: IntegerOptional | None = None,
        cache_node_ids_to_remove: CacheNodeIdsList | None = None,
        az_mode: AZMode | None = None,
        new_availability_zones: PreferredAvailabilityZoneList | None = None,
        cache_security_group_names: CacheSecurityGroupNameList | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        preferred_maintenance_window: String | None = None,
        notification_topic_arn: String | None = None,
        cache_parameter_group_name: String | None = None,
        notification_topic_status: String | None = None,
        apply_immediately: Boolean | None = None,
        engine: String | None = None,
        engine_version: String | None = None,
        auto_minor_version_upgrade: BooleanOptional | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        snapshot_window: String | None = None,
        cache_node_type: String | None = None,
        auth_token: String | None = None,
        auth_token_update_strategy: AuthTokenUpdateStrategyType | None = None,
        log_delivery_configurations: LogDeliveryConfigurationRequestList | None = None,
        ip_discovery: IpDiscovery | None = None,
        scale_config: ScaleConfig | None = None,
        **kwargs,
    ) -> ModifyCacheClusterResult:
        raise NotImplementedError

    @handler("ModifyCacheParameterGroup")
    def modify_cache_parameter_group(
        self,
        context: RequestContext,
        cache_parameter_group_name: String,
        parameter_name_values: ParameterNameValueList,
        **kwargs,
    ) -> CacheParameterGroupNameMessage:
        raise NotImplementedError

    @handler("ModifyCacheSubnetGroup")
    def modify_cache_subnet_group(
        self,
        context: RequestContext,
        cache_subnet_group_name: String,
        cache_subnet_group_description: String | None = None,
        subnet_ids: SubnetIdentifierList | None = None,
        **kwargs,
    ) -> ModifyCacheSubnetGroupResult:
        raise NotImplementedError

    @handler("ModifyGlobalReplicationGroup")
    def modify_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        apply_immediately: Boolean,
        cache_node_type: String | None = None,
        engine: String | None = None,
        engine_version: String | None = None,
        cache_parameter_group_name: String | None = None,
        global_replication_group_description: String | None = None,
        automatic_failover_enabled: BooleanOptional | None = None,
        **kwargs,
    ) -> ModifyGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("ModifyReplicationGroup")
    def modify_replication_group(
        self,
        context: RequestContext,
        replication_group_id: String,
        replication_group_description: String | None = None,
        primary_cluster_id: String | None = None,
        snapshotting_cluster_id: String | None = None,
        automatic_failover_enabled: BooleanOptional | None = None,
        multi_az_enabled: BooleanOptional | None = None,
        node_group_id: String | None = None,
        cache_security_group_names: CacheSecurityGroupNameList | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        preferred_maintenance_window: String | None = None,
        notification_topic_arn: String | None = None,
        cache_parameter_group_name: String | None = None,
        notification_topic_status: String | None = None,
        apply_immediately: Boolean | None = None,
        engine: String | None = None,
        engine_version: String | None = None,
        auto_minor_version_upgrade: BooleanOptional | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        snapshot_window: String | None = None,
        cache_node_type: String | None = None,
        auth_token: String | None = None,
        auth_token_update_strategy: AuthTokenUpdateStrategyType | None = None,
        user_group_ids_to_add: UserGroupIdList | None = None,
        user_group_ids_to_remove: UserGroupIdList | None = None,
        remove_user_groups: BooleanOptional | None = None,
        log_delivery_configurations: LogDeliveryConfigurationRequestList | None = None,
        ip_discovery: IpDiscovery | None = None,
        transit_encryption_enabled: BooleanOptional | None = None,
        transit_encryption_mode: TransitEncryptionMode | None = None,
        cluster_mode: ClusterMode | None = None,
        **kwargs,
    ) -> ModifyReplicationGroupResult:
        raise NotImplementedError

    @handler("ModifyReplicationGroupShardConfiguration")
    def modify_replication_group_shard_configuration(
        self,
        context: RequestContext,
        replication_group_id: String,
        node_group_count: Integer,
        apply_immediately: Boolean,
        resharding_configuration: ReshardingConfigurationList | None = None,
        node_groups_to_remove: NodeGroupsToRemoveList | None = None,
        node_groups_to_retain: NodeGroupsToRetainList | None = None,
        **kwargs,
    ) -> ModifyReplicationGroupShardConfigurationResult:
        raise NotImplementedError

    @handler("ModifyServerlessCache")
    def modify_serverless_cache(
        self,
        context: RequestContext,
        serverless_cache_name: String,
        description: String | None = None,
        cache_usage_limits: CacheUsageLimits | None = None,
        remove_user_group: BooleanOptional | None = None,
        user_group_id: String | None = None,
        security_group_ids: SecurityGroupIdsList | None = None,
        snapshot_retention_limit: IntegerOptional | None = None,
        daily_snapshot_time: String | None = None,
        engine: String | None = None,
        major_engine_version: String | None = None,
        **kwargs,
    ) -> ModifyServerlessCacheResponse:
        raise NotImplementedError

    @handler("ModifyUser")
    def modify_user(
        self,
        context: RequestContext,
        user_id: UserId,
        access_string: AccessString | None = None,
        append_access_string: AccessString | None = None,
        passwords: PasswordListInput | None = None,
        no_password_required: BooleanOptional | None = None,
        authentication_mode: AuthenticationMode | None = None,
        engine: EngineType | None = None,
        **kwargs,
    ) -> User:
        raise NotImplementedError

    @handler("ModifyUserGroup")
    def modify_user_group(
        self,
        context: RequestContext,
        user_group_id: String,
        user_ids_to_add: UserIdListInput | None = None,
        user_ids_to_remove: UserIdListInput | None = None,
        engine: EngineType | None = None,
        **kwargs,
    ) -> UserGroup:
        raise NotImplementedError

    @handler("PurchaseReservedCacheNodesOffering")
    def purchase_reserved_cache_nodes_offering(
        self,
        context: RequestContext,
        reserved_cache_nodes_offering_id: String,
        reserved_cache_node_id: String | None = None,
        cache_node_count: IntegerOptional | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> PurchaseReservedCacheNodesOfferingResult:
        raise NotImplementedError

    @handler("RebalanceSlotsInGlobalReplicationGroup")
    def rebalance_slots_in_global_replication_group(
        self,
        context: RequestContext,
        global_replication_group_id: String,
        apply_immediately: Boolean,
        **kwargs,
    ) -> RebalanceSlotsInGlobalReplicationGroupResult:
        raise NotImplementedError

    @handler("RebootCacheCluster")
    def reboot_cache_cluster(
        self,
        context: RequestContext,
        cache_cluster_id: String,
        cache_node_ids_to_reboot: CacheNodeIdsList,
        **kwargs,
    ) -> RebootCacheClusterResult:
        raise NotImplementedError

    @handler("RemoveTagsFromResource")
    def remove_tags_from_resource(
        self, context: RequestContext, resource_name: String, tag_keys: KeyList, **kwargs
    ) -> TagListMessage:
        raise NotImplementedError

    @handler("ResetCacheParameterGroup")
    def reset_cache_parameter_group(
        self,
        context: RequestContext,
        cache_parameter_group_name: String,
        reset_all_parameters: Boolean | None = None,
        parameter_name_values: ParameterNameValueList | None = None,
        **kwargs,
    ) -> CacheParameterGroupNameMessage:
        raise NotImplementedError

    @handler("RevokeCacheSecurityGroupIngress")
    def revoke_cache_security_group_ingress(
        self,
        context: RequestContext,
        cache_security_group_name: String,
        ec2_security_group_name: String,
        ec2_security_group_owner_id: String,
        **kwargs,
    ) -> RevokeCacheSecurityGroupIngressResult:
        raise NotImplementedError

    @handler("StartMigration")
    def start_migration(
        self,
        context: RequestContext,
        replication_group_id: String,
        customer_node_endpoint_list: CustomerNodeEndpointList,
        **kwargs,
    ) -> StartMigrationResponse:
        raise NotImplementedError

    @handler("TestFailover")
    def test_failover(
        self,
        context: RequestContext,
        replication_group_id: String,
        node_group_id: AllowedNodeGroupId,
        **kwargs,
    ) -> TestFailoverResult:
        raise NotImplementedError

    @handler("TestMigration")
    def test_migration(
        self,
        context: RequestContext,
        replication_group_id: String,
        customer_node_endpoint_list: CustomerNodeEndpointList,
        **kwargs,
    ) -> TestMigrationResponse:
        raise NotImplementedError
