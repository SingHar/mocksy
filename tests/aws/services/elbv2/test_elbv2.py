"""ELBv2 Application Load Balancers (issue #14).

Targets are local HTTP servers registered as ``ip`` targets, so these tests do
not need Docker. ``test_elbv2_ecs.py`` covers ECS services behind a load balancer.
"""

import re
import time

import pytest
import requests
from pytest_httpserver import HTTPServer
from werkzeug import Response as WerkzeugResponse

from localstack import config
from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

GATEWAY = config.internal_service_url()


def _get(lb: dict, path: str = "/", scheme: str = "http", method: str = "GET", **kwargs):
    url = config.internal_service_url(protocol=scheme) + path
    headers = {"Host": lb["DNSName"], **kwargs.pop("headers", {})}
    return requests.request(
        method, url, headers=headers, allow_redirects=False, verify=False, timeout=10, **kwargs
    )


class Target:
    """A local HTTP server that answers with its name; ``healthy = False`` fails health checks.

    Each target listens on its own loopback address: Moto keys targets by ID, so two
    targets on one IP with different ports would replace each other.
    """

    _next_ip = 10

    def __init__(self, name: str):
        self.name = name
        self.healthy = True
        self.requests: list[dict] = []
        Target._next_ip += 1
        self.ip = f"127.0.0.{Target._next_ip}"
        self.server = HTTPServer(host=self.ip, port=0)
        self.server.expect_request("/health").respond_with_handler(self._health)
        self.server.expect_request(re.compile(".*")).respond_with_handler(self._handle)
        self.server.start()

    @property
    def port(self) -> int:
        return self.server.port

    def _health(self, request):
        return WerkzeugResponse(
            "ok" if self.healthy else "down", status=200 if self.healthy else 500
        )

    def _handle(self, request):
        self.requests.append(dict(request.headers))
        return WerkzeugResponse(f"{self.name} {request.method} {request.full_path.rstrip('?')}")

    def stop(self):
        if self.server.is_running():
            self.server.stop()


@pytest.fixture
def targets():
    created = []

    def _create(name: str) -> Target:
        target = Target(name)
        created.append(target)
        return target

    yield _create
    for target in created:
        target.stop()


@pytest.fixture
def load_balancer(aws_client, cleanups):
    """A load balancer in the default VPC; returns (load balancer, vpc ID)."""
    ec2, elbv2 = aws_client.ec2, aws_client.elbv2
    vpc_id = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0][
        "VpcId"
    ]
    subnets = [
        s["SubnetId"]
        for s in ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])["Subnets"]
    ][:2]
    lb = elbv2.create_load_balancer(Name=f"lb-{short_uid()}", Subnets=subnets)["LoadBalancers"][0]
    cleanups.append(lambda: elbv2.delete_load_balancer(LoadBalancerArn=lb["LoadBalancerArn"]))
    return lb, vpc_id


@pytest.fixture
def target_group(aws_client, load_balancer, cleanups):
    _, vpc_id = load_balancer

    def _create(*members: Target, **kwargs) -> str:
        kwargs.setdefault("HealthCheckPath", "/health")
        kwargs.setdefault("HealthCheckIntervalSeconds", 5)
        kwargs.setdefault("HealthCheckTimeoutSeconds", 2)
        kwargs.setdefault("HealthyThresholdCount", 2)
        kwargs.setdefault("UnhealthyThresholdCount", 2)
        arn = aws_client.elbv2.create_target_group(
            Name=f"tg-{short_uid()}",
            Protocol="HTTP",
            Port=80,
            VpcId=vpc_id,
            TargetType="ip",
            **kwargs,
        )["TargetGroups"][0]["TargetGroupArn"]
        cleanups.append(lambda: aws_client.elbv2.delete_target_group(TargetGroupArn=arn))
        if members:
            aws_client.elbv2.register_targets(
                TargetGroupArn=arn, Targets=[{"Id": t.ip, "Port": t.port} for t in members]
            )
        return arn

    return _create


def _listener(aws_client, lb: dict, default_actions: list, protocol: str = "HTTP", port: int = 0):
    kwargs = {}
    if protocol == "HTTPS":
        certificate = aws_client.acm.request_certificate(DomainName=lb["DNSName"])
        kwargs["Certificates"] = [{"CertificateArn": certificate["CertificateArn"]}]
    return aws_client.elbv2.create_listener(
        LoadBalancerArn=lb["LoadBalancerArn"],
        Protocol=protocol,
        Port=port or (443 if protocol == "HTTPS" else 80),
        DefaultActions=default_actions,
        **kwargs,
    )["Listeners"][0]["ListenerArn"]


def _forward(arn: str) -> list:
    return [{"Type": "forward", "TargetGroupArn": arn}]


def _wait_health(aws_client, arn: str, expected: list[str]) -> list[dict]:
    def _check():
        descriptions = aws_client.elbv2.describe_target_health(TargetGroupArn=arn)[
            "TargetHealthDescriptions"
        ]
        assert sorted(d["TargetHealth"]["State"] for d in descriptions) == sorted(expected)
        return descriptions

    return retry(_check, retries=40, sleep=1)


class TestElbv2Routing:
    @markers.aws.only_localstack
    def test_dns_name_and_round_robin(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        assert lb["DNSName"].endswith(".elb.localhost.localstack.cloud")
        a, b = targets("a"), targets("b")
        arn = target_group(a, b)
        _listener(aws_client, lb, _forward(arn))
        _wait_health(aws_client, arn, ["healthy", "healthy"])

        answers = {_get(lb, "/items?x=1").text for _ in range(4)}
        assert answers == {"a GET /items?x=1", "b GET /items?x=1"}

        headers = a.requests[-1]
        assert headers["Host"] == lb["DNSName"]
        assert headers["X-Forwarded-Proto"] == "http"
        assert headers["X-Forwarded-Port"] == "80"
        assert headers["X-Forwarded-For"]
        assert headers["X-Amzn-Trace-Id"].startswith("Root=1-")

    @markers.aws.only_localstack
    def test_rules_and_actions(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        api, admin = targets("api"), targets("admin")
        api_arn, admin_arn = target_group(api), target_group(admin)
        listener = _listener(
            aws_client,
            lb,
            [
                {
                    "Type": "fixed-response",
                    "FixedResponseConfig": {
                        "StatusCode": "404",
                        "ContentType": "text/plain",
                        "MessageBody": "no route",
                    },
                }
            ],
        )
        rules = [
            (
                10,
                [{"Field": "path-pattern", "PathPatternConfig": {"Values": ["/api/*"]}}],
                _forward(api_arn),
            ),
            (
                20,
                [
                    {"Field": "path-pattern", "Values": ["/admin*"]},
                    {
                        "Field": "http-header",
                        "HttpHeaderConfig": {"HttpHeaderName": "X-Role", "Values": ["admin"]},
                    },
                ],
                _forward(admin_arn),
            ),
            (
                30,
                [
                    {
                        "Field": "http-request-method",
                        "HttpRequestMethodConfig": {"Values": ["DELETE"]},
                    }
                ],
                [
                    {
                        "Type": "fixed-response",
                        "FixedResponseConfig": {"StatusCode": "405", "ContentType": "text/plain"},
                    }
                ],
            ),
            (
                40,
                [
                    {
                        "Field": "query-string",
                        "QueryStringConfig": {"Values": [{"Key": "legacy", "Value": "1"}]},
                    }
                ],
                [
                    {
                        "Type": "redirect",
                        "RedirectConfig": {
                            "Protocol": "HTTPS",
                            "Port": "443",
                            "Path": "/v2/#{path}",
                            "Query": "#{query}",
                            "StatusCode": "HTTP_301",
                        },
                    }
                ],
            ),
            (
                50,
                [
                    {
                        "Field": "host-header",
                        "HostHeaderConfig": {"Values": ["*.elb.localhost.localstack.cloud"]},
                    }
                ],
                _forward(api_arn),
            ),
        ]
        for priority, conditions, actions in rules:
            aws_client.elbv2.create_rule(
                ListenerArn=listener, Priority=priority, Conditions=conditions, Actions=actions
            )
        _wait_health(aws_client, api_arn, ["healthy"])

        assert _get(lb, "/api/users").text == "api GET /api/users"
        assert (
            _get(lb, "/admin/panel", headers={"X-Role": "admin"}).text == "admin GET /admin/panel"
        )
        # the header condition fails, so the host-header rule (50) matches
        assert _get(lb, "/admin/panel").text == "api GET /admin/panel"
        assert _get(lb, "/x", method="DELETE").status_code == 405

        redirect = _get(lb, "/old?legacy=1")
        assert redirect.status_code == 301
        assert redirect.headers["Location"] == f"https://{lb['DNSName']}/v2/old?legacy=1"

        # without a matching rule the default action answers
        aws_client.elbv2.delete_rule(
            RuleArn=next(
                r["RuleArn"]
                for r in aws_client.elbv2.describe_rules(ListenerArn=listener)["Rules"]
                if r["Priority"] == "50"
            )
        )
        fallback = _get(lb, "/nothing")
        assert (fallback.status_code, fallback.text) == (404, "no route")

    @markers.aws.only_localstack
    def test_weighted_forward(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        blue, green = targets("blue"), targets("green")
        blue_arn, green_arn = target_group(blue), target_group(green)
        _listener(
            aws_client,
            lb,
            [
                {
                    "Type": "forward",
                    "ForwardConfig": {
                        "TargetGroups": [
                            {"TargetGroupArn": blue_arn, "Weight": 0},
                            {"TargetGroupArn": green_arn, "Weight": 1},
                        ]
                    },
                }
            ],
        )
        assert {_get(lb, "/").text for _ in range(5)} == {"green GET /"}

    @markers.aws.only_localstack
    def test_health_checks(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        good, bad = targets("good"), targets("bad")
        arn = target_group(good, bad)
        _listener(aws_client, lb, _forward(arn))
        _wait_health(aws_client, arn, ["healthy", "healthy"])

        bad.healthy = False
        descriptions = _wait_health(aws_client, arn, ["healthy", "unhealthy"])
        unhealthy = next(d for d in descriptions if d["TargetHealth"]["State"] == "unhealthy")
        assert unhealthy["Target"]["Port"] == bad.port
        assert unhealthy["TargetHealth"]["Reason"] == "Target.ResponseCodeMismatch"
        assert {_get(lb, "/").text for _ in range(4)} == {"good GET /"}

        # all unhealthy: requests go to all targets (fail open), as in AWS
        good.healthy = False
        _wait_health(aws_client, arn, ["unhealthy", "unhealthy"])
        assert {_get(lb, "/").text for _ in range(4)} == {"good GET /", "bad GET /"}

    @markers.aws.only_localstack
    def test_errors(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        empty_arn = target_group()
        _listener(aws_client, lb, _forward(empty_arn))
        response = _get(lb, "/")
        assert response.status_code == 503
        assert "503 Service Temporarily Unavailable" in response.text

        dead = targets("dead")
        port = dead.port
        dead.stop()
        aws_client.elbv2.register_targets(
            TargetGroupArn=empty_arn, Targets=[{"Id": dead.ip, "Port": port}]
        )
        assert _get(lb, "/").status_code == 502

    @markers.aws.only_localstack
    def test_https_listener(self, aws_client, load_balancer, target_group, targets):
        lb, _ = load_balancer
        target = targets("tls")
        arn = target_group(target)
        _listener(aws_client, lb, _forward(arn), protocol="HTTPS")
        response = _get(lb, "/secure", scheme="https")
        assert response.text == "tls GET /secure"
        assert target.requests[-1]["X-Forwarded-Proto"] == "https"
        assert target.requests[-1]["X-Forwarded-Port"] == "443"

    @markers.aws.only_localstack
    def test_metrics(self, aws_client, load_balancer, target_group, targets, monkeypatch):
        monkeypatch.setattr(config, "ELBV2_METRICS_INTERVAL", 1)
        lb, _ = load_balancer
        target = targets("m")
        arn = target_group(target)
        _listener(aws_client, lb, _forward(arn))
        for _ in range(3):
            _get(lb, "/")
        dimension = lb["LoadBalancerArn"].split(":loadbalancer/", 1)[1]

        def _published():
            names = {
                m["MetricName"]
                for m in aws_client.cloudwatch.list_metrics(
                    Namespace="AWS/ApplicationELB",
                    Dimensions=[{"Name": "LoadBalancer", "Value": dimension}],
                )["Metrics"]
            }
            assert {"RequestCount", "TargetResponseTime", "HTTPCode_Target_2XX_Count"} <= names

        retry(_published, retries=20, sleep=1)


class TestElbv2Api:
    @markers.aws.unknown
    def test_target_health_of_unused_group(self, aws_client, load_balancer, target_group, targets):
        target = targets("unused")
        arn = target_group(target)
        time.sleep(1)
        health = aws_client.elbv2.describe_target_health(TargetGroupArn=arn)[
            "TargetHealthDescriptions"
        ]
        # no listener uses the group: AWS reports it as unused
        assert health[0]["TargetHealth"]["State"] == "unused"
        assert health[0]["TargetHealth"]["Reason"] == "Target.NotInUse"
