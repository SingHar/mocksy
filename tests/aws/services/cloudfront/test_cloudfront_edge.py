"""CloudFront distributions forward requests to their origins (issue #4, phase 2)."""

import pytest
import requests
from werkzeug import Response as WerkzeugResponse

from localstack import config
from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid

TRUSTED_SIGNERS = {"Enabled": False, "Quantity": 0}
FORWARDED = {"QueryString": False, "Cookies": {"Forward": "none"}}


def _get(distribution: dict, path: str, method: str = "GET", scheme: str = "http"):
    # requests go to mocksy's gateway with the distribution's domain as host
    url = config.internal_service_url(protocol=scheme) + path
    return requests.request(
        method,
        url,
        headers={"Host": distribution["DomainName"]},
        allow_redirects=False,
        verify=False,
        timeout=10,
    )


@pytest.fixture
def create_distribution(aws_client):
    created = []

    def _create(**config) -> dict:
        config.setdefault("CallerReference", short_uid())
        config.setdefault("Comment", "")
        config.setdefault("Enabled", True)
        distribution = aws_client.cloudfront.create_distribution(DistributionConfig=config)[
            "Distribution"
        ]
        created.append(distribution["Id"])
        return distribution

    yield _create

    for distribution_id in created:
        try:
            current = aws_client.cloudfront.get_distribution_config(Id=distribution_id)
            disabled = current["DistributionConfig"]
            disabled["Enabled"] = False
            etag = aws_client.cloudfront.update_distribution(
                Id=distribution_id, DistributionConfig=disabled, IfMatch=current["ETag"]
            )["ETag"]
            aws_client.cloudfront.delete_distribution(Id=distribution_id, IfMatch=etag)
        except Exception:
            pass


@pytest.fixture
def site_bucket(aws_client, s3_bucket):
    aws_client.s3.put_object(
        Bucket=s3_bucket, Key="index.html", Body=b"<h1>home</h1>", ContentType="text/html"
    )
    aws_client.s3.put_object(
        Bucket=s3_bucket, Key="assets/app.js", Body=b"console.log(1)", ContentType="text/javascript"
    )
    return s3_bucket


def _s3_origin(bucket: str) -> dict:
    return {
        "Id": "site",
        "DomainName": f"{bucket}.s3.us-east-1.amazonaws.com",
        "S3OriginConfig": {"OriginAccessIdentity": ""},
    }


def _http_origin(httpserver, **extra) -> dict:
    origin = {
        "Id": "api",
        "DomainName": httpserver.host,
        "CustomOriginConfig": {
            "HTTPPort": httpserver.port,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "http-only",
        },
    }
    origin.update(extra)
    return origin


def _behavior(origin_id: str, **extra) -> dict:
    behavior = {
        "TargetOriginId": origin_id,
        "ViewerProtocolPolicy": "allow-all",
        "MinTTL": 0,
        "ForwardedValues": FORWARDED,
        "TrustedSigners": TRUSTED_SIGNERS,
    }
    behavior.update(extra)
    return behavior


class TestCloudfrontEdge:
    @markers.aws.only_localstack
    def test_s3_origin_with_spa_fallback(self, aws_client, create_distribution, site_bucket):
        distribution = create_distribution(
            DefaultRootObject="index.html",
            Origins={"Quantity": 1, "Items": [_s3_origin(site_bucket)]},
            DefaultCacheBehavior=_behavior("site"),
            CustomErrorResponses={
                "Quantity": 1,
                "Items": [
                    {"ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "200"}
                ],
            },
        )
        assert distribution["DomainName"].endswith(".cloudfront.localhost.localstack.cloud")

        root = _get(distribution, "/")
        assert root.status_code == 200
        assert root.text == "<h1>home</h1>"
        assert root.headers["Content-Type"].startswith("text/html")

        asset = _get(distribution, "/assets/app.js")
        assert asset.text == "console.log(1)"

        fallback = _get(distribution, "/some/client/route")
        assert fallback.status_code == 200
        assert fallback.text == "<h1>home</h1>"

        # the configuration keeps the error responses (OpenTofu/Terraform read them back)
        stored = aws_client.cloudfront.get_distribution_config(Id=distribution["Id"])[
            "DistributionConfig"
        ]
        assert stored["CustomErrorResponses"]["Items"][0]["ResponsePagePath"] == "/index.html"
        assert stored["DefaultCacheBehavior"]["DefaultTTL"] == 86400

    @markers.aws.only_localstack
    def test_custom_origin_cache_and_invalidation(
        self, aws_client, create_distribution, site_bucket, httpserver
    ):
        calls = []

        def _handler(request):
            calls.append(dict(request.headers))
            return WerkzeugResponse(f"api {request.path}", headers={"Cache-Control": "max-age=60"})

        httpserver.expect_request("/api/health").respond_with_handler(_handler)
        origin = _http_origin(
            httpserver,
            CustomHeaders={
                "Quantity": 1,
                "Items": [{"HeaderName": "X-Origin-Secret", "HeaderValue": "s3cret"}],
            },
        )
        distribution = create_distribution(
            Origins={"Quantity": 2, "Items": [_s3_origin(site_bucket), origin]},
            DefaultCacheBehavior=_behavior("site"),
            CacheBehaviors={"Quantity": 1, "Items": [_behavior("api", PathPattern="/api/*")]},
        )

        first = _get(distribution, "/api/health")
        assert first.text == "api /api/health"
        assert first.headers["X-Cache"] == "Miss from cloudfront"
        assert calls[0]["X-Origin-Secret"] == "s3cret"
        assert calls[0]["Host"] == httpserver.host

        second = _get(distribution, "/api/health")
        assert second.headers["X-Cache"] == "Hit from cloudfront"
        assert len(calls) == 1

        aws_client.cloudfront.create_invalidation(
            DistributionId=distribution["Id"],
            InvalidationBatch={
                "Paths": {"Quantity": 1, "Items": ["/api/*"]},
                "CallerReference": short_uid(),
            },
        )
        third = _get(distribution, "/api/health")
        assert third.headers["X-Cache"] == "Miss from cloudfront"
        assert len(calls) == 2

        # the default behaviour still goes to S3
        assert _get(distribution, "/index.html").text == "<h1>home</h1>"

    @markers.aws.only_localstack
    def test_viewer_protocol_and_methods(self, create_distribution, site_bucket):
        distribution = create_distribution(
            Origins={"Quantity": 1, "Items": [_s3_origin(site_bucket)]},
            DefaultCacheBehavior=_behavior("site", ViewerProtocolPolicy="redirect-to-https"),
        )
        redirect = _get(distribution, "/index.html")
        assert redirect.status_code == 301
        assert redirect.headers["Location"].startswith(f"https://{distribution['DomainName']}")

        assert _get(distribution, "/index.html", scheme="https").status_code == 200
        assert _get(distribution, "/index.html", method="POST", scheme="https").status_code == 403

    @markers.aws.only_localstack
    def test_disabled_distribution(self, create_distribution, site_bucket):
        distribution = create_distribution(
            Enabled=False,
            Origins={"Quantity": 1, "Items": [_s3_origin(site_bucket)]},
            DefaultCacheBehavior=_behavior("site"),
        )
        assert _get(distribution, "/index.html").status_code == 403
