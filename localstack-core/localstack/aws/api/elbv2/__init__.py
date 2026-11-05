from datetime import datetime
from enum import StrEnum
from typing import TypedDict

from localstack.aws.api import RequestContext, ServiceException, ServiceRequest, handler

ActionOrder = int
AllocationId = str
AlpnPolicyValue = str
AuthenticateCognitoActionAuthenticationRequestParamName = str
AuthenticateCognitoActionAuthenticationRequestParamValue = str
AuthenticateCognitoActionScope = str
AuthenticateCognitoActionSessionCookieName = str
AuthenticateCognitoActionUserPoolArn = str
AuthenticateCognitoActionUserPoolClientId = str
AuthenticateCognitoActionUserPoolDomain = str
AuthenticateOidcActionAuthenticationRequestParamName = str
AuthenticateOidcActionAuthenticationRequestParamValue = str
AuthenticateOidcActionAuthorizationEndpoint = str
AuthenticateOidcActionClientId = str
AuthenticateOidcActionClientSecret = str
AuthenticateOidcActionIssuer = str
AuthenticateOidcActionScope = str
AuthenticateOidcActionSessionCookieName = str
AuthenticateOidcActionTokenEndpoint = str
AuthenticateOidcActionUseExistingClientSecret = bool
AuthenticateOidcActionUserInfoEndpoint = str
CanonicalHostedZoneId = str
CapacityUnits = int
CapacityUnitsDouble = float
CertificateArn = str
CipherName = str
CipherPriority = int
ConditionFieldName = str
CustomerOwnedIpv4Pool = str
DNSName = str
DecreaseRequestsRemaining = int
Default = bool
Description = str
EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic = str
FixedResponseActionContentType = str
FixedResponseActionMessage = str
FixedResponseActionStatusCode = str
GrpcCode = str
HealthCheckEnabled = bool
HealthCheckIntervalSeconds = int
HealthCheckPort = str
HealthCheckThresholdCount = int
HealthCheckTimeoutSeconds = int
HttpCode = str
HttpHeaderConditionName = str
IPv6Address = str
IgnoreClientCertificateExpiry = bool
IpAddress = str
IpamPoolId = str
IsDefault = bool
JwtValidationActionAdditionalClaimName = str
JwtValidationActionAdditionalClaimValue = str
JwtValidationActionIssuer = str
JwtValidationActionJwksEndpoint = str
ListenerArn = str
ListenerAttributeKey = str
ListenerAttributeValue = str
LoadBalancerArn = str
LoadBalancerAttributeKey = str
LoadBalancerAttributeValue = str
LoadBalancerName = str
Location = str
Marker = str
Max = str
Mode = str
Name = str
NumberOfCaCertificates = int
OutpostId = str
PageSize = int
Path = str
Policy = str
Port = int
PrivateIPv4Address = str
ProtocolVersion = str
QuicServerId = str
RedirectActionHost = str
RedirectActionPath = str
RedirectActionPort = str
RedirectActionProtocol = str
RedirectActionQuery = str
ResetCapacityReservation = bool
ResetTransforms = bool
ResourceArn = str
RuleArn = str
RulePriority = int
S3Bucket = str
S3Key = str
S3ObjectVersion = str
SecurityGroupId = str
SourceNatIpv6Prefix = str
SslPolicyName = str
SslProtocol = str
StateReason = str
String = str
StringValue = str
SubnetId = str
TagKey = str
TagValue = str
TargetControlPort = int
TargetGroupArn = str
TargetGroupAttributeKey = str
TargetGroupAttributeValue = str
TargetGroupName = str
TargetGroupStickinessDurationSeconds = int
TargetGroupStickinessEnabled = bool
TargetGroupWeight = int
TargetId = str
TrustStoreArn = str
TrustStoreAssociationResourceArn = str
TrustStoreName = str
VpcId = str
ZoneName = str


class ActionTypeEnum(StrEnum):
    forward = "forward"
    authenticate_oidc = "authenticate-oidc"
    authenticate_cognito = "authenticate-cognito"
    redirect = "redirect"
    fixed_response = "fixed-response"
    jwt_validation = "jwt-validation"


class AdvertiseTrustStoreCaNamesEnum(StrEnum):
    on = "on"
    off = "off"


class AnomalyResultEnum(StrEnum):
    anomalous = "anomalous"
    normal = "normal"


class AuthenticateCognitoActionConditionalBehaviorEnum(StrEnum):
    deny = "deny"
    allow = "allow"
    authenticate = "authenticate"


class AuthenticateOidcActionConditionalBehaviorEnum(StrEnum):
    deny = "deny"
    allow = "allow"
    authenticate = "authenticate"


class CapacityReservationStateEnum(StrEnum):
    provisioned = "provisioned"
    pending = "pending"
    rebalancing = "rebalancing"
    failed = "failed"


class DescribeTargetHealthInputIncludeEnum(StrEnum):
    AnomalyDetection = "AnomalyDetection"
    All = "All"


class EnablePrefixForIpv6SourceNatEnum(StrEnum):
    on = "on"
    off = "off"


class EnforceSecurityGroupInboundRulesOnPrivateLinkTrafficEnum(StrEnum):
    on = "on"
    off = "off"


class IpAddressType(StrEnum):
    ipv4 = "ipv4"
    dualstack = "dualstack"
    dualstack_without_public_ipv4 = "dualstack-without-public-ipv4"


class JwtValidationActionAdditionalClaimFormatEnum(StrEnum):
    single_string = "single-string"
    string_array = "string-array"
    space_separated_values = "space-separated-values"


class LoadBalancerSchemeEnum(StrEnum):
    internet_facing = "internet-facing"
    internal = "internal"


class LoadBalancerStateEnum(StrEnum):
    active = "active"
    provisioning = "provisioning"
    active_impaired = "active_impaired"
    failed = "failed"


class LoadBalancerTypeEnum(StrEnum):
    application = "application"
    network = "network"
    gateway = "gateway"


class MitigationInEffectEnum(StrEnum):
    yes = "yes"
    no = "no"


class ProtocolEnum(StrEnum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    TCP = "TCP"
    TLS = "TLS"
    UDP = "UDP"
    TCP_UDP = "TCP_UDP"
    GENEVE = "GENEVE"
    QUIC = "QUIC"
    TCP_QUIC = "TCP_QUIC"


class RedirectActionStatusCodeEnum(StrEnum):
    HTTP_301 = "HTTP_301"
    HTTP_302 = "HTTP_302"


class RemoveIpamPoolEnum(StrEnum):
    ipv4 = "ipv4"


class RevocationType(StrEnum):
    CRL = "CRL"


class TargetAdministrativeOverrideReasonEnum(StrEnum):
    AdministrativeOverride_Unknown = "AdministrativeOverride.Unknown"
    AdministrativeOverride_NoOverride = "AdministrativeOverride.NoOverride"
    AdministrativeOverride_ZonalShiftActive = "AdministrativeOverride.ZonalShiftActive"
    AdministrativeOverride_ZonalShiftDelegatedToDns = (
        "AdministrativeOverride.ZonalShiftDelegatedToDns"
    )


class TargetAdministrativeOverrideStateEnum(StrEnum):
    unknown = "unknown"
    no_override = "no_override"
    zonal_shift_active = "zonal_shift_active"
    zonal_shift_delegated_to_dns = "zonal_shift_delegated_to_dns"


class TargetGroupIpAddressTypeEnum(StrEnum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"


class TargetHealthReasonEnum(StrEnum):
    Elb_RegistrationInProgress = "Elb.RegistrationInProgress"
    Elb_InitialHealthChecking = "Elb.InitialHealthChecking"
    Target_ResponseCodeMismatch = "Target.ResponseCodeMismatch"
    Target_Timeout = "Target.Timeout"
    Target_FailedHealthChecks = "Target.FailedHealthChecks"
    Target_NotRegistered = "Target.NotRegistered"
    Target_NotInUse = "Target.NotInUse"
    Target_DeregistrationInProgress = "Target.DeregistrationInProgress"
    Target_InvalidState = "Target.InvalidState"
    Target_IpUnusable = "Target.IpUnusable"
    Target_HealthCheckDisabled = "Target.HealthCheckDisabled"
    Elb_InternalError = "Elb.InternalError"


class TargetHealthStateEnum(StrEnum):
    initial = "initial"
    healthy = "healthy"
    unhealthy = "unhealthy"
    unhealthy_draining = "unhealthy.draining"
    unused = "unused"
    draining = "draining"
    unavailable = "unavailable"


class TargetTypeEnum(StrEnum):
    instance = "instance"
    ip = "ip"
    lambda_ = "lambda"
    alb = "alb"


class TransformTypeEnum(StrEnum):
    host_header_rewrite = "host-header-rewrite"
    url_rewrite = "url-rewrite"


class TrustStoreAssociationStatusEnum(StrEnum):
    active = "active"
    removed = "removed"


class TrustStoreStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CREATING = "CREATING"


class ALPNPolicyNotSupportedException(ServiceException):
    code: str = "ALPNPolicyNotFound"
    sender_fault: bool = True
    status_code: int = 400


class AllocationIdNotFoundException(ServiceException):
    code: str = "AllocationIdNotFound"
    sender_fault: bool = True
    status_code: int = 400


class AvailabilityZoneNotSupportedException(ServiceException):
    code: str = "AvailabilityZoneNotSupported"
    sender_fault: bool = True
    status_code: int = 400


class CaCertificatesBundleNotFoundException(ServiceException):
    code: str = "CaCertificatesBundleNotFound"
    sender_fault: bool = True
    status_code: int = 400


class CapacityDecreaseRequestsLimitExceededException(ServiceException):
    code: str = "CapacityDecreaseRequestLimitExceeded"
    sender_fault: bool = True
    status_code: int = 400


class CapacityReservationPendingException(ServiceException):
    code: str = "CapacityReservationPending"
    sender_fault: bool = True
    status_code: int = 400


class CapacityUnitsLimitExceededException(ServiceException):
    code: str = "CapacityUnitsLimitExceeded"
    sender_fault: bool = True
    status_code: int = 400


class CertificateNotFoundException(ServiceException):
    code: str = "CertificateNotFound"
    sender_fault: bool = True
    status_code: int = 400


class DeleteAssociationSameAccountException(ServiceException):
    code: str = "DeleteAssociationSameAccount"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateListenerException(ServiceException):
    code: str = "DuplicateListener"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateLoadBalancerNameException(ServiceException):
    code: str = "DuplicateLoadBalancerName"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateTagKeysException(ServiceException):
    code: str = "DuplicateTagKeys"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateTargetGroupNameException(ServiceException):
    code: str = "DuplicateTargetGroupName"
    sender_fault: bool = True
    status_code: int = 400


class DuplicateTrustStoreNameException(ServiceException):
    code: str = "DuplicateTrustStoreName"
    sender_fault: bool = True
    status_code: int = 400


class HealthUnavailableException(ServiceException):
    code: str = "HealthUnavailable"
    sender_fault: bool = False
    status_code: int = 500


class IncompatibleProtocolsException(ServiceException):
    code: str = "IncompatibleProtocols"
    sender_fault: bool = True
    status_code: int = 400


class InsufficientCapacityException(ServiceException):
    code: str = "InsufficientCapacity"
    sender_fault: bool = False
    status_code: int = 500


class InvalidCaCertificatesBundleException(ServiceException):
    code: str = "InvalidCaCertificatesBundle"
    sender_fault: bool = True
    status_code: int = 400


class InvalidConfigurationRequestException(ServiceException):
    code: str = "InvalidConfigurationRequest"
    sender_fault: bool = True
    status_code: int = 400


class InvalidLoadBalancerActionException(ServiceException):
    code: str = "InvalidLoadBalancerAction"
    sender_fault: bool = True
    status_code: int = 400


class InvalidRevocationContentException(ServiceException):
    code: str = "InvalidRevocationContent"
    sender_fault: bool = True
    status_code: int = 400


class InvalidSchemeException(ServiceException):
    code: str = "InvalidScheme"
    sender_fault: bool = True
    status_code: int = 400


class InvalidSecurityGroupException(ServiceException):
    code: str = "InvalidSecurityGroup"
    sender_fault: bool = True
    status_code: int = 400


class InvalidSubnetException(ServiceException):
    code: str = "InvalidSubnet"
    sender_fault: bool = True
    status_code: int = 400


class InvalidTargetException(ServiceException):
    code: str = "InvalidTarget"
    sender_fault: bool = True
    status_code: int = 400


class ListenerNotFoundException(ServiceException):
    code: str = "ListenerNotFound"
    sender_fault: bool = True
    status_code: int = 400


class LoadBalancerNotFoundException(ServiceException):
    code: str = "LoadBalancerNotFound"
    sender_fault: bool = True
    status_code: int = 400


class OperationNotPermittedException(ServiceException):
    code: str = "OperationNotPermitted"
    sender_fault: bool = True
    status_code: int = 400


class PriorRequestNotCompleteException(ServiceException):
    code: str = "PriorRequestNotComplete"
    sender_fault: bool = True
    status_code: int = 429


class PriorityInUseException(ServiceException):
    code: str = "PriorityInUse"
    sender_fault: bool = True
    status_code: int = 400


class ResourceInUseException(ServiceException):
    code: str = "ResourceInUse"
    sender_fault: bool = True
    status_code: int = 400


class ResourceNotFoundException(ServiceException):
    code: str = "ResourceNotFound"
    sender_fault: bool = True
    status_code: int = 400


class RevocationContentNotFoundException(ServiceException):
    code: str = "RevocationContentNotFound"
    sender_fault: bool = True
    status_code: int = 400


class RevocationIdNotFoundException(ServiceException):
    code: str = "RevocationIdNotFound"
    sender_fault: bool = True
    status_code: int = 400


class RuleNotFoundException(ServiceException):
    code: str = "RuleNotFound"
    sender_fault: bool = True
    status_code: int = 400


class SSLPolicyNotFoundException(ServiceException):
    code: str = "SSLPolicyNotFound"
    sender_fault: bool = True
    status_code: int = 400


class SubnetNotFoundException(ServiceException):
    code: str = "SubnetNotFound"
    sender_fault: bool = True
    status_code: int = 400


class TargetGroupAssociationLimitException(ServiceException):
    code: str = "TargetGroupAssociationLimit"
    sender_fault: bool = True
    status_code: int = 400


class TargetGroupNotFoundException(ServiceException):
    code: str = "TargetGroupNotFound"
    sender_fault: bool = True
    status_code: int = 400


class TooManyActionsException(ServiceException):
    code: str = "TooManyActions"
    sender_fault: bool = True
    status_code: int = 400


class TooManyCertificatesException(ServiceException):
    code: str = "TooManyCertificates"
    sender_fault: bool = True
    status_code: int = 400


class TooManyListenersException(ServiceException):
    code: str = "TooManyListeners"
    sender_fault: bool = True
    status_code: int = 400


class TooManyLoadBalancersException(ServiceException):
    code: str = "TooManyLoadBalancers"
    sender_fault: bool = True
    status_code: int = 400


class TooManyRegistrationsForTargetIdException(ServiceException):
    code: str = "TooManyRegistrationsForTargetId"
    sender_fault: bool = True
    status_code: int = 400


class TooManyRulesException(ServiceException):
    code: str = "TooManyRules"
    sender_fault: bool = True
    status_code: int = 400


class TooManyTagsException(ServiceException):
    code: str = "TooManyTags"
    sender_fault: bool = True
    status_code: int = 400


class TooManyTargetGroupsException(ServiceException):
    code: str = "TooManyTargetGroups"
    sender_fault: bool = True
    status_code: int = 400


class TooManyTargetsException(ServiceException):
    code: str = "TooManyTargets"
    sender_fault: bool = True
    status_code: int = 400


class TooManyTrustStoreRevocationEntriesException(ServiceException):
    code: str = "TooManyTrustStoreRevocationEntries"
    sender_fault: bool = True
    status_code: int = 400


class TooManyTrustStoresException(ServiceException):
    code: str = "TooManyTrustStores"
    sender_fault: bool = True
    status_code: int = 400


class TooManyUniqueTargetGroupsPerLoadBalancerException(ServiceException):
    code: str = "TooManyUniqueTargetGroupsPerLoadBalancer"
    sender_fault: bool = True
    status_code: int = 400


class TrustStoreAssociationNotFoundException(ServiceException):
    code: str = "AssociationNotFound"
    sender_fault: bool = True
    status_code: int = 400


class TrustStoreInUseException(ServiceException):
    code: str = "TrustStoreInUse"
    sender_fault: bool = True
    status_code: int = 400


class TrustStoreNotFoundException(ServiceException):
    code: str = "TrustStoreNotFound"
    sender_fault: bool = True
    status_code: int = 400


class TrustStoreNotReadyException(ServiceException):
    code: str = "TrustStoreNotReady"
    sender_fault: bool = True
    status_code: int = 400


class UnsupportedProtocolException(ServiceException):
    code: str = "UnsupportedProtocol"
    sender_fault: bool = True
    status_code: int = 400


JwtValidationActionAdditionalClaimValues = list[JwtValidationActionAdditionalClaimValue]


class JwtValidationActionAdditionalClaim(TypedDict, total=False):
    Format: JwtValidationActionAdditionalClaimFormatEnum
    Name: JwtValidationActionAdditionalClaimName
    Values: JwtValidationActionAdditionalClaimValues


JwtValidationActionAdditionalClaims = list[JwtValidationActionAdditionalClaim]


class JwtValidationActionConfig(TypedDict, total=False):
    JwksEndpoint: JwtValidationActionJwksEndpoint
    Issuer: JwtValidationActionIssuer
    AdditionalClaims: JwtValidationActionAdditionalClaims | None


class TargetGroupStickinessConfig(TypedDict, total=False):
    Enabled: TargetGroupStickinessEnabled | None
    DurationSeconds: TargetGroupStickinessDurationSeconds | None


class TargetGroupTuple(TypedDict, total=False):
    TargetGroupArn: TargetGroupArn | None
    Weight: TargetGroupWeight | None


TargetGroupList = list[TargetGroupTuple]


class ForwardActionConfig(TypedDict, total=False):
    TargetGroups: TargetGroupList | None
    TargetGroupStickinessConfig: TargetGroupStickinessConfig | None


class FixedResponseActionConfig(TypedDict, total=False):
    MessageBody: FixedResponseActionMessage | None
    StatusCode: FixedResponseActionStatusCode
    ContentType: FixedResponseActionContentType | None


class RedirectActionConfig(TypedDict, total=False):
    Protocol: RedirectActionProtocol | None
    Port: RedirectActionPort | None
    Host: RedirectActionHost | None
    Path: RedirectActionPath | None
    Query: RedirectActionQuery | None
    StatusCode: RedirectActionStatusCodeEnum


AuthenticateCognitoActionAuthenticationRequestExtraParams = dict[
    AuthenticateCognitoActionAuthenticationRequestParamName,
    AuthenticateCognitoActionAuthenticationRequestParamValue,
]
AuthenticateCognitoActionSessionTimeout = int


class AuthenticateCognitoActionConfig(TypedDict, total=False):
    UserPoolArn: AuthenticateCognitoActionUserPoolArn
    UserPoolClientId: AuthenticateCognitoActionUserPoolClientId
    UserPoolDomain: AuthenticateCognitoActionUserPoolDomain
    SessionCookieName: AuthenticateCognitoActionSessionCookieName | None
    Scope: AuthenticateCognitoActionScope | None
    SessionTimeout: AuthenticateCognitoActionSessionTimeout | None
    AuthenticationRequestExtraParams: (
        AuthenticateCognitoActionAuthenticationRequestExtraParams | None
    )
    OnUnauthenticatedRequest: AuthenticateCognitoActionConditionalBehaviorEnum | None


AuthenticateOidcActionAuthenticationRequestExtraParams = dict[
    AuthenticateOidcActionAuthenticationRequestParamName,
    AuthenticateOidcActionAuthenticationRequestParamValue,
]
AuthenticateOidcActionSessionTimeout = int


class AuthenticateOidcActionConfig(TypedDict, total=False):
    Issuer: AuthenticateOidcActionIssuer
    AuthorizationEndpoint: AuthenticateOidcActionAuthorizationEndpoint
    TokenEndpoint: AuthenticateOidcActionTokenEndpoint
    UserInfoEndpoint: AuthenticateOidcActionUserInfoEndpoint
    ClientId: AuthenticateOidcActionClientId
    ClientSecret: AuthenticateOidcActionClientSecret | None
    SessionCookieName: AuthenticateOidcActionSessionCookieName | None
    Scope: AuthenticateOidcActionScope | None
    SessionTimeout: AuthenticateOidcActionSessionTimeout | None
    AuthenticationRequestExtraParams: AuthenticateOidcActionAuthenticationRequestExtraParams | None
    OnUnauthenticatedRequest: AuthenticateOidcActionConditionalBehaviorEnum | None
    UseExistingClientSecret: AuthenticateOidcActionUseExistingClientSecret | None


class Action(TypedDict, total=False):
    Type: ActionTypeEnum
    TargetGroupArn: TargetGroupArn | None
    AuthenticateOidcConfig: AuthenticateOidcActionConfig | None
    AuthenticateCognitoConfig: AuthenticateCognitoActionConfig | None
    Order: ActionOrder | None
    RedirectConfig: RedirectActionConfig | None
    FixedResponseConfig: FixedResponseActionConfig | None
    ForwardConfig: ForwardActionConfig | None
    JwtValidationConfig: JwtValidationActionConfig | None


Actions = list[Action]


class Certificate(TypedDict, total=False):
    CertificateArn: CertificateArn | None
    IsDefault: Default | None


CertificateList = list[Certificate]


class AddListenerCertificatesInput(ServiceRequest):
    ListenerArn: ListenerArn
    Certificates: CertificateList


class AddListenerCertificatesOutput(TypedDict, total=False):
    Certificates: CertificateList | None


class Tag(TypedDict, total=False):
    Key: TagKey
    Value: TagValue | None


TagList = list[Tag]
ResourceArns = list[ResourceArn]


class AddTagsInput(ServiceRequest):
    ResourceArns: ResourceArns
    Tags: TagList


class AddTagsOutput(TypedDict, total=False):
    pass


class RevocationContent(TypedDict, total=False):
    S3Bucket: S3Bucket | None
    S3Key: S3Key | None
    S3ObjectVersion: S3ObjectVersion | None
    RevocationType: RevocationType | None


RevocationContents = list[RevocationContent]


class AddTrustStoreRevocationsInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    RevocationContents: RevocationContents | None


NumberOfRevokedEntries = int
RevocationId = int


class TrustStoreRevocation(TypedDict, total=False):
    TrustStoreArn: TrustStoreArn | None
    RevocationId: RevocationId | None
    RevocationType: RevocationType | None
    NumberOfRevokedEntries: NumberOfRevokedEntries | None


TrustStoreRevocations = list[TrustStoreRevocation]


class AddTrustStoreRevocationsOutput(TypedDict, total=False):
    TrustStoreRevocations: TrustStoreRevocations | None


class AdministrativeOverride(TypedDict, total=False):
    State: TargetAdministrativeOverrideStateEnum | None
    Reason: TargetAdministrativeOverrideReasonEnum | None
    Description: Description | None


AlpnPolicyName = list[AlpnPolicyValue]


class AnomalyDetection(TypedDict, total=False):
    Result: AnomalyResultEnum | None
    MitigationInEffect: MitigationInEffectEnum | None


SourceNatIpv6Prefixes = list[SourceNatIpv6Prefix]


class LoadBalancerAddress(TypedDict, total=False):
    IpAddress: IpAddress | None
    AllocationId: AllocationId | None
    PrivateIPv4Address: PrivateIPv4Address | None
    IPv6Address: IPv6Address | None


LoadBalancerAddresses = list[LoadBalancerAddress]


class AvailabilityZone(TypedDict, total=False):
    ZoneName: ZoneName | None
    SubnetId: SubnetId | None
    OutpostId: OutpostId | None
    LoadBalancerAddresses: LoadBalancerAddresses | None
    SourceNatIpv6Prefixes: SourceNatIpv6Prefixes | None


AvailabilityZones = list[AvailabilityZone]


class CapacityReservationStatus(TypedDict, total=False):
    Code: CapacityReservationStateEnum | None
    Reason: StateReason | None


class Cipher(TypedDict, total=False):
    Name: CipherName | None
    Priority: CipherPriority | None


Ciphers = list[Cipher]


class MutualAuthenticationAttributes(TypedDict, total=False):
    Mode: Mode | None
    TrustStoreArn: TrustStoreArn | None
    IgnoreClientCertificateExpiry: IgnoreClientCertificateExpiry | None
    TrustStoreAssociationStatus: TrustStoreAssociationStatusEnum | None
    AdvertiseTrustStoreCaNames: AdvertiseTrustStoreCaNamesEnum | None


class CreateListenerInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    Protocol: ProtocolEnum | None
    Port: Port | None
    SslPolicy: SslPolicyName | None
    Certificates: CertificateList | None
    DefaultActions: Actions
    AlpnPolicy: AlpnPolicyName | None
    Tags: TagList | None
    MutualAuthentication: MutualAuthenticationAttributes | None


class Listener(TypedDict, total=False):
    ListenerArn: ListenerArn | None
    LoadBalancerArn: LoadBalancerArn | None
    Port: Port | None
    Protocol: ProtocolEnum | None
    Certificates: CertificateList | None
    SslPolicy: SslPolicyName | None
    DefaultActions: Actions | None
    AlpnPolicy: AlpnPolicyName | None
    MutualAuthentication: MutualAuthenticationAttributes | None


Listeners = list[Listener]


class CreateListenerOutput(TypedDict, total=False):
    Listeners: Listeners | None


class IpamPools(TypedDict, total=False):
    Ipv4IpamPoolId: IpamPoolId | None


SecurityGroups = list[SecurityGroupId]


class SubnetMapping(TypedDict, total=False):
    SubnetId: SubnetId | None
    AllocationId: AllocationId | None
    PrivateIPv4Address: PrivateIPv4Address | None
    IPv6Address: IPv6Address | None
    SourceNatIpv6Prefix: SourceNatIpv6Prefix | None


SubnetMappings = list[SubnetMapping]
Subnets = list[SubnetId]


class CreateLoadBalancerInput(ServiceRequest):
    Name: LoadBalancerName
    Subnets: Subnets | None
    SubnetMappings: SubnetMappings | None
    SecurityGroups: SecurityGroups | None
    Scheme: LoadBalancerSchemeEnum | None
    Tags: TagList | None
    Type: LoadBalancerTypeEnum | None
    IpAddressType: IpAddressType | None
    CustomerOwnedIpv4Pool: CustomerOwnedIpv4Pool | None
    EnablePrefixForIpv6SourceNat: EnablePrefixForIpv6SourceNatEnum | None
    IpamPools: IpamPools | None


class LoadBalancerState(TypedDict, total=False):
    Code: LoadBalancerStateEnum | None
    Reason: StateReason | None


CreatedTime = datetime


class LoadBalancer(TypedDict, total=False):
    LoadBalancerArn: LoadBalancerArn | None
    DNSName: DNSName | None
    CanonicalHostedZoneId: CanonicalHostedZoneId | None
    CreatedTime: CreatedTime | None
    LoadBalancerName: LoadBalancerName | None
    Scheme: LoadBalancerSchemeEnum | None
    VpcId: VpcId | None
    State: LoadBalancerState | None
    Type: LoadBalancerTypeEnum | None
    AvailabilityZones: AvailabilityZones | None
    SecurityGroups: SecurityGroups | None
    IpAddressType: IpAddressType | None
    CustomerOwnedIpv4Pool: CustomerOwnedIpv4Pool | None
    EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic: (
        EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic | None
    )
    EnablePrefixForIpv6SourceNat: EnablePrefixForIpv6SourceNatEnum | None
    IpamPools: IpamPools | None


LoadBalancers = list[LoadBalancer]


class CreateLoadBalancerOutput(TypedDict, total=False):
    LoadBalancers: LoadBalancers | None


class RewriteConfig(TypedDict, total=False):
    Regex: StringValue
    Replace: StringValue


RewriteConfigList = list[RewriteConfig]


class UrlRewriteConfig(TypedDict, total=False):
    Rewrites: RewriteConfigList | None


class HostHeaderRewriteConfig(TypedDict, total=False):
    Rewrites: RewriteConfigList | None


class RuleTransform(TypedDict, total=False):
    Type: TransformTypeEnum
    HostHeaderRewriteConfig: HostHeaderRewriteConfig | None
    UrlRewriteConfig: UrlRewriteConfig | None


RuleTransformList = list[RuleTransform]
ListOfString = list[StringValue]


class SourceIpConditionConfig(TypedDict, total=False):
    Values: ListOfString | None


class HttpRequestMethodConditionConfig(TypedDict, total=False):
    Values: ListOfString | None


class QueryStringKeyValuePair(TypedDict, total=False):
    Key: StringValue | None
    Value: StringValue | None


QueryStringKeyValuePairList = list[QueryStringKeyValuePair]


class QueryStringConditionConfig(TypedDict, total=False):
    Values: QueryStringKeyValuePairList | None


class HttpHeaderConditionConfig(TypedDict, total=False):
    HttpHeaderName: HttpHeaderConditionName | None
    Values: ListOfString | None
    RegexValues: ListOfString | None


class PathPatternConditionConfig(TypedDict, total=False):
    Values: ListOfString | None
    RegexValues: ListOfString | None


class HostHeaderConditionConfig(TypedDict, total=False):
    Values: ListOfString | None
    RegexValues: ListOfString | None


class RuleCondition(TypedDict, total=False):
    Field: ConditionFieldName | None
    Values: ListOfString | None
    HostHeaderConfig: HostHeaderConditionConfig | None
    PathPatternConfig: PathPatternConditionConfig | None
    HttpHeaderConfig: HttpHeaderConditionConfig | None
    QueryStringConfig: QueryStringConditionConfig | None
    HttpRequestMethodConfig: HttpRequestMethodConditionConfig | None
    SourceIpConfig: SourceIpConditionConfig | None
    RegexValues: ListOfString | None


RuleConditionList = list[RuleCondition]


class CreateRuleInput(ServiceRequest):
    ListenerArn: ListenerArn
    Conditions: RuleConditionList
    Priority: RulePriority
    Actions: Actions
    Tags: TagList | None
    Transforms: RuleTransformList | None


class Rule(TypedDict, total=False):
    RuleArn: RuleArn | None
    Priority: String | None
    Conditions: RuleConditionList | None
    Actions: Actions | None
    IsDefault: IsDefault | None
    Transforms: RuleTransformList | None


Rules = list[Rule]


class CreateRuleOutput(TypedDict, total=False):
    Rules: Rules | None


class Matcher(TypedDict, total=False):
    HttpCode: HttpCode | None
    GrpcCode: GrpcCode | None


class CreateTargetGroupInput(ServiceRequest):
    Name: TargetGroupName
    Protocol: ProtocolEnum | None
    ProtocolVersion: ProtocolVersion | None
    Port: Port | None
    VpcId: VpcId | None
    HealthCheckProtocol: ProtocolEnum | None
    HealthCheckPort: HealthCheckPort | None
    HealthCheckEnabled: HealthCheckEnabled | None
    HealthCheckPath: Path | None
    HealthCheckIntervalSeconds: HealthCheckIntervalSeconds | None
    HealthCheckTimeoutSeconds: HealthCheckTimeoutSeconds | None
    HealthyThresholdCount: HealthCheckThresholdCount | None
    UnhealthyThresholdCount: HealthCheckThresholdCount | None
    Matcher: Matcher | None
    TargetType: TargetTypeEnum | None
    Tags: TagList | None
    IpAddressType: TargetGroupIpAddressTypeEnum | None
    TargetControlPort: TargetControlPort | None


LoadBalancerArns = list[LoadBalancerArn]


class TargetGroup(TypedDict, total=False):
    TargetGroupArn: TargetGroupArn | None
    TargetGroupName: TargetGroupName | None
    Protocol: ProtocolEnum | None
    Port: Port | None
    VpcId: VpcId | None
    HealthCheckProtocol: ProtocolEnum | None
    HealthCheckPort: HealthCheckPort | None
    HealthCheckEnabled: HealthCheckEnabled | None
    HealthCheckIntervalSeconds: HealthCheckIntervalSeconds | None
    HealthCheckTimeoutSeconds: HealthCheckTimeoutSeconds | None
    HealthyThresholdCount: HealthCheckThresholdCount | None
    UnhealthyThresholdCount: HealthCheckThresholdCount | None
    HealthCheckPath: Path | None
    Matcher: Matcher | None
    LoadBalancerArns: LoadBalancerArns | None
    TargetType: TargetTypeEnum | None
    ProtocolVersion: ProtocolVersion | None
    IpAddressType: TargetGroupIpAddressTypeEnum | None
    TargetControlPort: TargetControlPort | None


TargetGroups = list[TargetGroup]


class CreateTargetGroupOutput(TypedDict, total=False):
    TargetGroups: TargetGroups | None


class CreateTrustStoreInput(ServiceRequest):
    Name: TrustStoreName
    CaCertificatesBundleS3Bucket: S3Bucket
    CaCertificatesBundleS3Key: S3Key
    CaCertificatesBundleS3ObjectVersion: S3ObjectVersion | None
    Tags: TagList | None


TotalRevokedEntries = int


class TrustStore(TypedDict, total=False):
    Name: TrustStoreName | None
    TrustStoreArn: TrustStoreArn | None
    Status: TrustStoreStatus | None
    NumberOfCaCertificates: NumberOfCaCertificates | None
    TotalRevokedEntries: TotalRevokedEntries | None


TrustStores = list[TrustStore]


class CreateTrustStoreOutput(TypedDict, total=False):
    TrustStores: TrustStores | None


class DeleteListenerInput(ServiceRequest):
    ListenerArn: ListenerArn


class DeleteListenerOutput(TypedDict, total=False):
    pass


class DeleteLoadBalancerInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn


class DeleteLoadBalancerOutput(TypedDict, total=False):
    pass


class DeleteRuleInput(ServiceRequest):
    RuleArn: RuleArn


class DeleteRuleOutput(TypedDict, total=False):
    pass


class DeleteSharedTrustStoreAssociationInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    ResourceArn: ResourceArn


class DeleteSharedTrustStoreAssociationOutput(TypedDict, total=False):
    pass


class DeleteTargetGroupInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn


class DeleteTargetGroupOutput(TypedDict, total=False):
    pass


class DeleteTrustStoreInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn


class DeleteTrustStoreOutput(TypedDict, total=False):
    pass


class TargetDescription(TypedDict, total=False):
    Id: TargetId
    Port: Port | None
    AvailabilityZone: ZoneName | None
    QuicServerId: QuicServerId | None


TargetDescriptions = list[TargetDescription]


class DeregisterTargetsInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn
    Targets: TargetDescriptions


class DeregisterTargetsOutput(TypedDict, total=False):
    pass


class DescribeAccountLimitsInput(ServiceRequest):
    Marker: Marker | None
    PageSize: PageSize | None


class Limit(TypedDict, total=False):
    Name: Name | None
    Max: Max | None


Limits = list[Limit]


class DescribeAccountLimitsOutput(TypedDict, total=False):
    Limits: Limits | None
    NextMarker: Marker | None


class DescribeCapacityReservationInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn


class ZonalCapacityReservationState(TypedDict, total=False):
    State: CapacityReservationStatus | None
    AvailabilityZone: ZoneName | None
    EffectiveCapacityUnits: CapacityUnitsDouble | None


ZonalCapacityReservationStates = list[ZonalCapacityReservationState]


class MinimumLoadBalancerCapacity(TypedDict, total=False):
    CapacityUnits: CapacityUnits | None


LastModifiedTime = datetime


class DescribeCapacityReservationOutput(TypedDict, total=False):
    LastModifiedTime: LastModifiedTime | None
    DecreaseRequestsRemaining: DecreaseRequestsRemaining | None
    MinimumLoadBalancerCapacity: MinimumLoadBalancerCapacity | None
    CapacityReservationState: ZonalCapacityReservationStates | None


class DescribeListenerAttributesInput(ServiceRequest):
    ListenerArn: ListenerArn


class ListenerAttribute(TypedDict, total=False):
    Key: ListenerAttributeKey | None
    Value: ListenerAttributeValue | None


ListenerAttributes = list[ListenerAttribute]


class DescribeListenerAttributesOutput(TypedDict, total=False):
    Attributes: ListenerAttributes | None


class DescribeListenerCertificatesInput(ServiceRequest):
    ListenerArn: ListenerArn
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeListenerCertificatesOutput(TypedDict, total=False):
    Certificates: CertificateList | None
    NextMarker: Marker | None


ListenerArns = list[ListenerArn]


class DescribeListenersInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn | None
    ListenerArns: ListenerArns | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeListenersOutput(TypedDict, total=False):
    Listeners: Listeners | None
    NextMarker: Marker | None


class DescribeLoadBalancerAttributesInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn


class LoadBalancerAttribute(TypedDict, total=False):
    Key: LoadBalancerAttributeKey | None
    Value: LoadBalancerAttributeValue | None


LoadBalancerAttributes = list[LoadBalancerAttribute]


class DescribeLoadBalancerAttributesOutput(TypedDict, total=False):
    Attributes: LoadBalancerAttributes | None


LoadBalancerNames = list[LoadBalancerName]


class DescribeLoadBalancersInput(ServiceRequest):
    LoadBalancerArns: LoadBalancerArns | None
    Names: LoadBalancerNames | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeLoadBalancersOutput(TypedDict, total=False):
    LoadBalancers: LoadBalancers | None
    NextMarker: Marker | None


RuleArns = list[RuleArn]


class DescribeRulesInput(ServiceRequest):
    ListenerArn: ListenerArn | None
    RuleArns: RuleArns | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeRulesOutput(TypedDict, total=False):
    Rules: Rules | None
    NextMarker: Marker | None


SslPolicyNames = list[SslPolicyName]


class DescribeSSLPoliciesInput(ServiceRequest):
    Names: SslPolicyNames | None
    Marker: Marker | None
    PageSize: PageSize | None
    LoadBalancerType: LoadBalancerTypeEnum | None


SslProtocols = list[SslProtocol]


class SslPolicy(TypedDict, total=False):
    SslProtocols: SslProtocols | None
    Ciphers: Ciphers | None
    Name: SslPolicyName | None
    SupportedLoadBalancerTypes: ListOfString | None


SslPolicies = list[SslPolicy]


class DescribeSSLPoliciesOutput(TypedDict, total=False):
    SslPolicies: SslPolicies | None
    NextMarker: Marker | None


class DescribeTagsInput(ServiceRequest):
    ResourceArns: ResourceArns


class TagDescription(TypedDict, total=False):
    ResourceArn: ResourceArn | None
    Tags: TagList | None


TagDescriptions = list[TagDescription]


class DescribeTagsOutput(TypedDict, total=False):
    TagDescriptions: TagDescriptions | None


class DescribeTargetGroupAttributesInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn


class TargetGroupAttribute(TypedDict, total=False):
    Key: TargetGroupAttributeKey | None
    Value: TargetGroupAttributeValue | None


TargetGroupAttributes = list[TargetGroupAttribute]


class DescribeTargetGroupAttributesOutput(TypedDict, total=False):
    Attributes: TargetGroupAttributes | None


TargetGroupNames = list[TargetGroupName]
TargetGroupArns = list[TargetGroupArn]


class DescribeTargetGroupsInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn | None
    TargetGroupArns: TargetGroupArns | None
    Names: TargetGroupNames | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeTargetGroupsOutput(TypedDict, total=False):
    TargetGroups: TargetGroups | None
    NextMarker: Marker | None


ListOfDescribeTargetHealthIncludeOptions = list[DescribeTargetHealthInputIncludeEnum]


class DescribeTargetHealthInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn
    Targets: TargetDescriptions | None
    Include: ListOfDescribeTargetHealthIncludeOptions | None


class TargetHealth(TypedDict, total=False):
    State: TargetHealthStateEnum | None
    Reason: TargetHealthReasonEnum | None
    Description: Description | None


class TargetHealthDescription(TypedDict, total=False):
    Target: TargetDescription | None
    HealthCheckPort: HealthCheckPort | None
    TargetHealth: TargetHealth | None
    AnomalyDetection: AnomalyDetection | None
    AdministrativeOverride: AdministrativeOverride | None


TargetHealthDescriptions = list[TargetHealthDescription]


class DescribeTargetHealthOutput(TypedDict, total=False):
    TargetHealthDescriptions: TargetHealthDescriptions | None


class DescribeTrustStoreAssociationsInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    Marker: Marker | None
    PageSize: PageSize | None


class TrustStoreAssociation(TypedDict, total=False):
    ResourceArn: TrustStoreAssociationResourceArn | None


TrustStoreAssociations = list[TrustStoreAssociation]


class DescribeTrustStoreAssociationsOutput(TypedDict, total=False):
    TrustStoreAssociations: TrustStoreAssociations | None
    NextMarker: Marker | None


class DescribeTrustStoreRevocation(TypedDict, total=False):
    TrustStoreArn: TrustStoreArn | None
    RevocationId: RevocationId | None
    RevocationType: RevocationType | None
    NumberOfRevokedEntries: NumberOfRevokedEntries | None


DescribeTrustStoreRevocationResponse = list[DescribeTrustStoreRevocation]
RevocationIds = list[RevocationId]


class DescribeTrustStoreRevocationsInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    RevocationIds: RevocationIds | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeTrustStoreRevocationsOutput(TypedDict, total=False):
    TrustStoreRevocations: DescribeTrustStoreRevocationResponse | None
    NextMarker: Marker | None


TrustStoreNames = list[TrustStoreName]
TrustStoreArns = list[TrustStoreArn]


class DescribeTrustStoresInput(ServiceRequest):
    TrustStoreArns: TrustStoreArns | None
    Names: TrustStoreNames | None
    Marker: Marker | None
    PageSize: PageSize | None


class DescribeTrustStoresOutput(TypedDict, total=False):
    TrustStores: TrustStores | None
    NextMarker: Marker | None


class GetResourcePolicyInput(ServiceRequest):
    ResourceArn: ResourceArn


class GetResourcePolicyOutput(TypedDict, total=False):
    Policy: Policy | None


class GetTrustStoreCaCertificatesBundleInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn


class GetTrustStoreCaCertificatesBundleOutput(TypedDict, total=False):
    Location: Location | None


class GetTrustStoreRevocationContentInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    RevocationId: RevocationId


class GetTrustStoreRevocationContentOutput(TypedDict, total=False):
    Location: Location | None


class ModifyCapacityReservationInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    MinimumLoadBalancerCapacity: MinimumLoadBalancerCapacity | None
    ResetCapacityReservation: ResetCapacityReservation | None


class ModifyCapacityReservationOutput(TypedDict, total=False):
    LastModifiedTime: LastModifiedTime | None
    DecreaseRequestsRemaining: DecreaseRequestsRemaining | None
    MinimumLoadBalancerCapacity: MinimumLoadBalancerCapacity | None
    CapacityReservationState: ZonalCapacityReservationStates | None


RemoveIpamPools = list[RemoveIpamPoolEnum]


class ModifyIpPoolsInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    IpamPools: IpamPools | None
    RemoveIpamPools: RemoveIpamPools | None


class ModifyIpPoolsOutput(TypedDict, total=False):
    IpamPools: IpamPools | None


class ModifyListenerAttributesInput(ServiceRequest):
    ListenerArn: ListenerArn
    Attributes: ListenerAttributes


class ModifyListenerAttributesOutput(TypedDict, total=False):
    Attributes: ListenerAttributes | None


class ModifyListenerInput(ServiceRequest):
    ListenerArn: ListenerArn
    Port: Port | None
    Protocol: ProtocolEnum | None
    SslPolicy: SslPolicyName | None
    Certificates: CertificateList | None
    DefaultActions: Actions | None
    AlpnPolicy: AlpnPolicyName | None
    MutualAuthentication: MutualAuthenticationAttributes | None


class ModifyListenerOutput(TypedDict, total=False):
    Listeners: Listeners | None


class ModifyLoadBalancerAttributesInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    Attributes: LoadBalancerAttributes


class ModifyLoadBalancerAttributesOutput(TypedDict, total=False):
    Attributes: LoadBalancerAttributes | None


class ModifyRuleInput(ServiceRequest):
    RuleArn: RuleArn
    Conditions: RuleConditionList | None
    Actions: Actions | None
    Transforms: RuleTransformList | None
    ResetTransforms: ResetTransforms | None


class ModifyRuleOutput(TypedDict, total=False):
    Rules: Rules | None


class ModifyTargetGroupAttributesInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn
    Attributes: TargetGroupAttributes


class ModifyTargetGroupAttributesOutput(TypedDict, total=False):
    Attributes: TargetGroupAttributes | None


class ModifyTargetGroupInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn
    HealthCheckProtocol: ProtocolEnum | None
    HealthCheckPort: HealthCheckPort | None
    HealthCheckPath: Path | None
    HealthCheckEnabled: HealthCheckEnabled | None
    HealthCheckIntervalSeconds: HealthCheckIntervalSeconds | None
    HealthCheckTimeoutSeconds: HealthCheckTimeoutSeconds | None
    HealthyThresholdCount: HealthCheckThresholdCount | None
    UnhealthyThresholdCount: HealthCheckThresholdCount | None
    Matcher: Matcher | None


class ModifyTargetGroupOutput(TypedDict, total=False):
    TargetGroups: TargetGroups | None


class ModifyTrustStoreInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    CaCertificatesBundleS3Bucket: S3Bucket
    CaCertificatesBundleS3Key: S3Key
    CaCertificatesBundleS3ObjectVersion: S3ObjectVersion | None


class ModifyTrustStoreOutput(TypedDict, total=False):
    TrustStores: TrustStores | None


class RegisterTargetsInput(ServiceRequest):
    TargetGroupArn: TargetGroupArn
    Targets: TargetDescriptions


class RegisterTargetsOutput(TypedDict, total=False):
    pass


class RemoveListenerCertificatesInput(ServiceRequest):
    ListenerArn: ListenerArn
    Certificates: CertificateList


class RemoveListenerCertificatesOutput(TypedDict, total=False):
    pass


TagKeys = list[TagKey]


class RemoveTagsInput(ServiceRequest):
    ResourceArns: ResourceArns
    TagKeys: TagKeys


class RemoveTagsOutput(TypedDict, total=False):
    pass


class RemoveTrustStoreRevocationsInput(ServiceRequest):
    TrustStoreArn: TrustStoreArn
    RevocationIds: RevocationIds


class RemoveTrustStoreRevocationsOutput(TypedDict, total=False):
    pass


class RulePriorityPair(TypedDict, total=False):
    RuleArn: RuleArn | None
    Priority: RulePriority | None


RulePriorityList = list[RulePriorityPair]


class SetIpAddressTypeInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    IpAddressType: IpAddressType


class SetIpAddressTypeOutput(TypedDict, total=False):
    IpAddressType: IpAddressType | None


class SetRulePrioritiesInput(ServiceRequest):
    RulePriorities: RulePriorityList


class SetRulePrioritiesOutput(TypedDict, total=False):
    Rules: Rules | None


class SetSecurityGroupsInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    SecurityGroups: SecurityGroups
    EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic: (
        EnforceSecurityGroupInboundRulesOnPrivateLinkTrafficEnum | None
    )


class SetSecurityGroupsOutput(TypedDict, total=False):
    SecurityGroupIds: SecurityGroups | None
    EnforceSecurityGroupInboundRulesOnPrivateLinkTraffic: (
        EnforceSecurityGroupInboundRulesOnPrivateLinkTrafficEnum | None
    )


class SetSubnetsInput(ServiceRequest):
    LoadBalancerArn: LoadBalancerArn
    Subnets: Subnets | None
    SubnetMappings: SubnetMappings | None
    IpAddressType: IpAddressType | None
    EnablePrefixForIpv6SourceNat: EnablePrefixForIpv6SourceNatEnum | None


class SetSubnetsOutput(TypedDict, total=False):
    AvailabilityZones: AvailabilityZones | None
    IpAddressType: IpAddressType | None
    EnablePrefixForIpv6SourceNat: EnablePrefixForIpv6SourceNatEnum | None


class Elbv2Api:
    service: str = "elbv2"
    version: str = "2015-12-01"

    @handler("AddListenerCertificates")
    def add_listener_certificates(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        certificates: CertificateList,
        **kwargs,
    ) -> AddListenerCertificatesOutput:
        raise NotImplementedError

    @handler("AddTags")
    def add_tags(
        self, context: RequestContext, resource_arns: ResourceArns, tags: TagList, **kwargs
    ) -> AddTagsOutput:
        raise NotImplementedError

    @handler("AddTrustStoreRevocations")
    def add_trust_store_revocations(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        revocation_contents: RevocationContents | None = None,
        **kwargs,
    ) -> AddTrustStoreRevocationsOutput:
        raise NotImplementedError

    @handler("CreateListener")
    def create_listener(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        default_actions: Actions,
        protocol: ProtocolEnum | None = None,
        port: Port | None = None,
        ssl_policy: SslPolicyName | None = None,
        certificates: CertificateList | None = None,
        alpn_policy: AlpnPolicyName | None = None,
        tags: TagList | None = None,
        mutual_authentication: MutualAuthenticationAttributes | None = None,
        **kwargs,
    ) -> CreateListenerOutput:
        raise NotImplementedError

    @handler("CreateLoadBalancer", expand=False)
    def create_load_balancer(
        self, context: RequestContext, request: CreateLoadBalancerInput, **kwargs
    ) -> CreateLoadBalancerOutput:
        raise NotImplementedError

    @handler("CreateRule")
    def create_rule(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        conditions: RuleConditionList,
        priority: RulePriority,
        actions: Actions,
        tags: TagList | None = None,
        transforms: RuleTransformList | None = None,
        **kwargs,
    ) -> CreateRuleOutput:
        raise NotImplementedError

    @handler("CreateTargetGroup")
    def create_target_group(
        self,
        context: RequestContext,
        name: TargetGroupName,
        protocol: ProtocolEnum | None = None,
        protocol_version: ProtocolVersion | None = None,
        port: Port | None = None,
        vpc_id: VpcId | None = None,
        health_check_protocol: ProtocolEnum | None = None,
        health_check_port: HealthCheckPort | None = None,
        health_check_enabled: HealthCheckEnabled | None = None,
        health_check_path: Path | None = None,
        health_check_interval_seconds: HealthCheckIntervalSeconds | None = None,
        health_check_timeout_seconds: HealthCheckTimeoutSeconds | None = None,
        healthy_threshold_count: HealthCheckThresholdCount | None = None,
        unhealthy_threshold_count: HealthCheckThresholdCount | None = None,
        matcher: Matcher | None = None,
        target_type: TargetTypeEnum | None = None,
        tags: TagList | None = None,
        ip_address_type: TargetGroupIpAddressTypeEnum | None = None,
        target_control_port: TargetControlPort | None = None,
        **kwargs,
    ) -> CreateTargetGroupOutput:
        raise NotImplementedError

    @handler("CreateTrustStore")
    def create_trust_store(
        self,
        context: RequestContext,
        name: TrustStoreName,
        ca_certificates_bundle_s3_bucket: S3Bucket,
        ca_certificates_bundle_s3_key: S3Key,
        ca_certificates_bundle_s3_object_version: S3ObjectVersion | None = None,
        tags: TagList | None = None,
        **kwargs,
    ) -> CreateTrustStoreOutput:
        raise NotImplementedError

    @handler("DeleteListener")
    def delete_listener(
        self, context: RequestContext, listener_arn: ListenerArn, **kwargs
    ) -> DeleteListenerOutput:
        raise NotImplementedError

    @handler("DeleteLoadBalancer")
    def delete_load_balancer(
        self, context: RequestContext, load_balancer_arn: LoadBalancerArn, **kwargs
    ) -> DeleteLoadBalancerOutput:
        raise NotImplementedError

    @handler("DeleteRule")
    def delete_rule(self, context: RequestContext, rule_arn: RuleArn, **kwargs) -> DeleteRuleOutput:
        raise NotImplementedError

    @handler("DeleteSharedTrustStoreAssociation")
    def delete_shared_trust_store_association(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        resource_arn: ResourceArn,
        **kwargs,
    ) -> DeleteSharedTrustStoreAssociationOutput:
        raise NotImplementedError

    @handler("DeleteTargetGroup")
    def delete_target_group(
        self, context: RequestContext, target_group_arn: TargetGroupArn, **kwargs
    ) -> DeleteTargetGroupOutput:
        raise NotImplementedError

    @handler("DeleteTrustStore")
    def delete_trust_store(
        self, context: RequestContext, trust_store_arn: TrustStoreArn, **kwargs
    ) -> DeleteTrustStoreOutput:
        raise NotImplementedError

    @handler("DeregisterTargets")
    def deregister_targets(
        self,
        context: RequestContext,
        target_group_arn: TargetGroupArn,
        targets: TargetDescriptions,
        **kwargs,
    ) -> DeregisterTargetsOutput:
        raise NotImplementedError

    @handler("DescribeAccountLimits")
    def describe_account_limits(
        self,
        context: RequestContext,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeAccountLimitsOutput:
        raise NotImplementedError

    @handler("DescribeCapacityReservation")
    def describe_capacity_reservation(
        self, context: RequestContext, load_balancer_arn: LoadBalancerArn, **kwargs
    ) -> DescribeCapacityReservationOutput:
        raise NotImplementedError

    @handler("DescribeListenerAttributes")
    def describe_listener_attributes(
        self, context: RequestContext, listener_arn: ListenerArn, **kwargs
    ) -> DescribeListenerAttributesOutput:
        raise NotImplementedError

    @handler("DescribeListenerCertificates")
    def describe_listener_certificates(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeListenerCertificatesOutput:
        raise NotImplementedError

    @handler("DescribeListeners")
    def describe_listeners(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn | None = None,
        listener_arns: ListenerArns | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeListenersOutput:
        raise NotImplementedError

    @handler("DescribeLoadBalancerAttributes")
    def describe_load_balancer_attributes(
        self, context: RequestContext, load_balancer_arn: LoadBalancerArn, **kwargs
    ) -> DescribeLoadBalancerAttributesOutput:
        raise NotImplementedError

    @handler("DescribeLoadBalancers")
    def describe_load_balancers(
        self,
        context: RequestContext,
        load_balancer_arns: LoadBalancerArns | None = None,
        names: LoadBalancerNames | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeLoadBalancersOutput:
        raise NotImplementedError

    @handler("DescribeRules")
    def describe_rules(
        self,
        context: RequestContext,
        listener_arn: ListenerArn | None = None,
        rule_arns: RuleArns | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeRulesOutput:
        raise NotImplementedError

    @handler("DescribeSSLPolicies")
    def describe_ssl_policies(
        self,
        context: RequestContext,
        names: SslPolicyNames | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        load_balancer_type: LoadBalancerTypeEnum | None = None,
        **kwargs,
    ) -> DescribeSSLPoliciesOutput:
        raise NotImplementedError

    @handler("DescribeTags")
    def describe_tags(
        self, context: RequestContext, resource_arns: ResourceArns, **kwargs
    ) -> DescribeTagsOutput:
        raise NotImplementedError

    @handler("DescribeTargetGroupAttributes")
    def describe_target_group_attributes(
        self, context: RequestContext, target_group_arn: TargetGroupArn, **kwargs
    ) -> DescribeTargetGroupAttributesOutput:
        raise NotImplementedError

    @handler("DescribeTargetGroups")
    def describe_target_groups(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn | None = None,
        target_group_arns: TargetGroupArns | None = None,
        names: TargetGroupNames | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeTargetGroupsOutput:
        raise NotImplementedError

    @handler("DescribeTargetHealth")
    def describe_target_health(
        self,
        context: RequestContext,
        target_group_arn: TargetGroupArn,
        targets: TargetDescriptions | None = None,
        include: ListOfDescribeTargetHealthIncludeOptions | None = None,
        **kwargs,
    ) -> DescribeTargetHealthOutput:
        raise NotImplementedError

    @handler("DescribeTrustStoreAssociations")
    def describe_trust_store_associations(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeTrustStoreAssociationsOutput:
        raise NotImplementedError

    @handler("DescribeTrustStoreRevocations")
    def describe_trust_store_revocations(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        revocation_ids: RevocationIds | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeTrustStoreRevocationsOutput:
        raise NotImplementedError

    @handler("DescribeTrustStores")
    def describe_trust_stores(
        self,
        context: RequestContext,
        trust_store_arns: TrustStoreArns | None = None,
        names: TrustStoreNames | None = None,
        marker: Marker | None = None,
        page_size: PageSize | None = None,
        **kwargs,
    ) -> DescribeTrustStoresOutput:
        raise NotImplementedError

    @handler("GetResourcePolicy")
    def get_resource_policy(
        self, context: RequestContext, resource_arn: ResourceArn, **kwargs
    ) -> GetResourcePolicyOutput:
        raise NotImplementedError

    @handler("GetTrustStoreCaCertificatesBundle")
    def get_trust_store_ca_certificates_bundle(
        self, context: RequestContext, trust_store_arn: TrustStoreArn, **kwargs
    ) -> GetTrustStoreCaCertificatesBundleOutput:
        raise NotImplementedError

    @handler("GetTrustStoreRevocationContent")
    def get_trust_store_revocation_content(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        revocation_id: RevocationId,
        **kwargs,
    ) -> GetTrustStoreRevocationContentOutput:
        raise NotImplementedError

    @handler("ModifyCapacityReservation")
    def modify_capacity_reservation(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        minimum_load_balancer_capacity: MinimumLoadBalancerCapacity | None = None,
        reset_capacity_reservation: ResetCapacityReservation | None = None,
        **kwargs,
    ) -> ModifyCapacityReservationOutput:
        raise NotImplementedError

    @handler("ModifyIpPools")
    def modify_ip_pools(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        ipam_pools: IpamPools | None = None,
        remove_ipam_pools: RemoveIpamPools | None = None,
        **kwargs,
    ) -> ModifyIpPoolsOutput:
        raise NotImplementedError

    @handler("ModifyListener")
    def modify_listener(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        port: Port | None = None,
        protocol: ProtocolEnum | None = None,
        ssl_policy: SslPolicyName | None = None,
        certificates: CertificateList | None = None,
        default_actions: Actions | None = None,
        alpn_policy: AlpnPolicyName | None = None,
        mutual_authentication: MutualAuthenticationAttributes | None = None,
        **kwargs,
    ) -> ModifyListenerOutput:
        raise NotImplementedError

    @handler("ModifyListenerAttributes")
    def modify_listener_attributes(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        attributes: ListenerAttributes,
        **kwargs,
    ) -> ModifyListenerAttributesOutput:
        raise NotImplementedError

    @handler("ModifyLoadBalancerAttributes")
    def modify_load_balancer_attributes(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        attributes: LoadBalancerAttributes,
        **kwargs,
    ) -> ModifyLoadBalancerAttributesOutput:
        raise NotImplementedError

    @handler("ModifyRule")
    def modify_rule(
        self,
        context: RequestContext,
        rule_arn: RuleArn,
        conditions: RuleConditionList | None = None,
        actions: Actions | None = None,
        transforms: RuleTransformList | None = None,
        reset_transforms: ResetTransforms | None = None,
        **kwargs,
    ) -> ModifyRuleOutput:
        raise NotImplementedError

    @handler("ModifyTargetGroup")
    def modify_target_group(
        self,
        context: RequestContext,
        target_group_arn: TargetGroupArn,
        health_check_protocol: ProtocolEnum | None = None,
        health_check_port: HealthCheckPort | None = None,
        health_check_path: Path | None = None,
        health_check_enabled: HealthCheckEnabled | None = None,
        health_check_interval_seconds: HealthCheckIntervalSeconds | None = None,
        health_check_timeout_seconds: HealthCheckTimeoutSeconds | None = None,
        healthy_threshold_count: HealthCheckThresholdCount | None = None,
        unhealthy_threshold_count: HealthCheckThresholdCount | None = None,
        matcher: Matcher | None = None,
        **kwargs,
    ) -> ModifyTargetGroupOutput:
        raise NotImplementedError

    @handler("ModifyTargetGroupAttributes")
    def modify_target_group_attributes(
        self,
        context: RequestContext,
        target_group_arn: TargetGroupArn,
        attributes: TargetGroupAttributes,
        **kwargs,
    ) -> ModifyTargetGroupAttributesOutput:
        raise NotImplementedError

    @handler("ModifyTrustStore")
    def modify_trust_store(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        ca_certificates_bundle_s3_bucket: S3Bucket,
        ca_certificates_bundle_s3_key: S3Key,
        ca_certificates_bundle_s3_object_version: S3ObjectVersion | None = None,
        **kwargs,
    ) -> ModifyTrustStoreOutput:
        raise NotImplementedError

    @handler("RegisterTargets")
    def register_targets(
        self,
        context: RequestContext,
        target_group_arn: TargetGroupArn,
        targets: TargetDescriptions,
        **kwargs,
    ) -> RegisterTargetsOutput:
        raise NotImplementedError

    @handler("RemoveListenerCertificates")
    def remove_listener_certificates(
        self,
        context: RequestContext,
        listener_arn: ListenerArn,
        certificates: CertificateList,
        **kwargs,
    ) -> RemoveListenerCertificatesOutput:
        raise NotImplementedError

    @handler("RemoveTags")
    def remove_tags(
        self, context: RequestContext, resource_arns: ResourceArns, tag_keys: TagKeys, **kwargs
    ) -> RemoveTagsOutput:
        raise NotImplementedError

    @handler("RemoveTrustStoreRevocations")
    def remove_trust_store_revocations(
        self,
        context: RequestContext,
        trust_store_arn: TrustStoreArn,
        revocation_ids: RevocationIds,
        **kwargs,
    ) -> RemoveTrustStoreRevocationsOutput:
        raise NotImplementedError

    @handler("SetIpAddressType")
    def set_ip_address_type(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        ip_address_type: IpAddressType,
        **kwargs,
    ) -> SetIpAddressTypeOutput:
        raise NotImplementedError

    @handler("SetRulePriorities")
    def set_rule_priorities(
        self, context: RequestContext, rule_priorities: RulePriorityList, **kwargs
    ) -> SetRulePrioritiesOutput:
        raise NotImplementedError

    @handler("SetSecurityGroups")
    def set_security_groups(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        security_groups: SecurityGroups,
        enforce_security_group_inbound_rules_on_private_link_traffic: EnforceSecurityGroupInboundRulesOnPrivateLinkTrafficEnum
        | None = None,
        **kwargs,
    ) -> SetSecurityGroupsOutput:
        raise NotImplementedError

    @handler("SetSubnets")
    def set_subnets(
        self,
        context: RequestContext,
        load_balancer_arn: LoadBalancerArn,
        subnets: Subnets | None = None,
        subnet_mappings: SubnetMappings | None = None,
        ip_address_type: IpAddressType | None = None,
        enable_prefix_for_ipv6_source_nat: EnablePrefixForIpv6SourceNatEnum | None = None,
        **kwargs,
    ) -> SetSubnetsOutput:
        raise NotImplementedError
