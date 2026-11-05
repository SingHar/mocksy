"""Serves CloudFront distributions on mocksy's gateway (issue #4, phase 2).

Each distribution's ``DomainName`` is ``<id>.cloudfront.<LOCALSTACK_HOST host>``,
for example ``e1abc2def3.cloudfront.localhost.localstack.cloud``. A request to
that host on mocksy's gateway (port 4566, HTTP or HTTPS) goes through these steps:

1. The cache behaviour is the first ``CacheBehaviors`` item whose
   ``PathPattern`` matches the path, else ``DefaultCacheBehavior``.
2. ``ViewerProtocolPolicy``: ``redirect-to-https`` answers HTTP with 301,
   ``https-only`` answers HTTP with 403.
3. Methods outside ``AllowedMethods`` get 403.
4. GET and HEAD responses come from the cache when they are fresh.
5. Otherwise the request goes to the origin:
   - S3 origin (``<bucket>.s3...amazonaws.com``): the object is read from
     mocksy's S3. ``/`` returns ``DefaultRootObject``.
   - Custom origin: the request is sent to ``<domain>:<port><OriginPath><path>``
     with the scheme from ``OriginProtocolPolicy`` and the origin's custom headers.
6. ``CustomErrorResponses`` replace origin errors (for example 403/404 to
   ``/index.html`` with 200 for single-page apps).
7. Responses carry ``X-Cache`` (``Hit``/``Miss from cloudfront``), ``Via`` and
   ``X-Amz-Cf-Id``. They are cached for their TTL: the origin's ``Cache-Control``
   ``s-maxage``/``max-age`` within ``MinTTL``..``MaxTTL``, else ``DefaultTTL``.

CreateInvalidation removes matching paths (``/images/*`` matches a prefix) from
the cache.
"""

from __future__ import annotations

import fnmatch
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

import requests
import urllib3
from rolo import Request

from localstack.aws.connect import connect_to
from localstack.http import Response
from localstack.utils.urls import localstack_host

LOG = logging.getLogger(__name__)

# custom origins are reached with verify=False (local origins use self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST_PATTERN = "<regex('[a-z0-9]+'):distribution_id>.cloudfront.<regex('.*'):server>"

# managed cache policy "CachingDisabled"
CACHING_DISABLED_POLICY = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
DEFAULT_TTL = 86400
MAX_TTL = 31536000
ERROR_CACHING_TTL = 10

_S3_DOMAIN = re.compile(r"^(?P<bucket>.+?)\.s3([.-][a-z0-9-]+)*\.amazonaws\.com$")
# headers that are not forwarded between client, CloudFront and origin
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
    "content-encoding",
}


def distribution_domain(distribution_id: str) -> str:
    return f"{distribution_id.lower()}.cloudfront.{localstack_host().host}"


@dataclass
class CachedResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    expires: float


class ResponseCache:
    """In-memory cache per distribution: (method, path with query) -> response."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, dict[tuple[str, str], CachedResponse]] = {}

    def get(self, distribution_id: str, key: tuple[str, str]) -> CachedResponse | None:
        with self._lock:
            entry = self._entries.get(distribution_id, {}).get(key)
            if entry and entry.expires > time.monotonic():
                return entry
            return None

    def put(self, distribution_id: str, key: tuple[str, str], entry: CachedResponse) -> None:
        with self._lock:
            self._entries.setdefault(distribution_id, {})[key] = entry

    def invalidate(self, distribution_id: str, paths: list[str]) -> None:
        with self._lock:
            entries = self._entries.get(distribution_id, {})
            for key in list(entries):
                path = key[1].split("?", 1)[0]
                if any(_invalidation_matches(pattern, path) for pattern in paths):
                    del entries[key]

    def clear(self, distribution_id: str | None = None) -> None:
        with self._lock:
            if distribution_id is None:
                self._entries.clear()
            else:
                self._entries.pop(distribution_id, None)


def _invalidation_matches(pattern: str, path: str) -> bool:
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return path == pattern


def _path_matches(pattern: str, path: str) -> bool:
    """CloudFront path patterns: ``*`` matches any characters (also ``/``), ``?`` one."""
    pattern = pattern if pattern.startswith("/") else f"/{pattern}"
    return fnmatch.fnmatchcase(path, pattern)


def _items(value: Any) -> list:
    """Return the list of an AWS ``{"Quantity": n, "Items": [...]}`` structure."""
    if not value:
        return []
    if isinstance(value, dict):
        return value.get("Items") or []
    return list(value)


class CloudFrontEdge:
    def __init__(self) -> None:
        self.cache = ResponseCache()

    # --------------------------------------------------------------- lookup

    def _find(self, distribution_id: str) -> tuple[str, str, dict[str, Any]] | None:
        """Return (account, ID, DistributionConfig) for a distribution ID (any case)."""
        from moto.cloudfront.models import cloudfront_backends

        wanted = distribution_id.upper()
        for account_id, regions in list(cloudfront_backends.items()):
            for backend in list(regions.values()):
                if wanted in backend.distributions:
                    client = connect_to(
                        aws_access_key_id=account_id, region_name="us-east-1"
                    ).cloudfront
                    config = client.get_distribution_config(Id=wanted)["DistributionConfig"]
                    return account_id, wanted, config
        return None

    # -------------------------------------------------------------- handler

    def __call__(self, request: Request, distribution_id: str, **kwargs) -> Response:
        try:
            return self._handle(request, distribution_id)
        except Exception as e:
            LOG.exception("CloudFront request to %s failed", distribution_id)
            return self._error(502, "Bad Gateway", f"The request could not be satisfied: {e}")

    def _handle(self, request: Request, distribution_id: str) -> Response:
        found = self._find(distribution_id)
        if not found:
            return self._error(
                404, "Not Found", f"No distribution {distribution_id} is configured."
            )
        account_id, dist_id, config = found
        if not config.get("Enabled", True):
            return self._error(403, "Forbidden", "The distribution is disabled.")

        path = request.path or "/"
        behavior = self._behavior(config, path)

        policy = behavior.get("ViewerProtocolPolicy", "allow-all")
        if request.scheme == "http" and policy != "allow-all":
            if policy == "redirect-to-https":
                location = f"https://{request.host}{request.full_path.rstrip('?')}"
                response = Response(status=301, headers={"Location": location})
                return self._decorate(response, dist_id, hit=False)
            return self._error(403, "Forbidden", "HTTPS is required.")

        allowed = _items(behavior.get("AllowedMethods")) or ["GET", "HEAD"]
        if request.method not in allowed:
            return self._error(
                403,
                "Forbidden",
                "This distribution is not configured to allow the HTTP request method.",
            )

        forward_query = self._forwards_query(behavior)
        query = request.query_string.decode() if forward_query else ""
        cache_key = (request.method, f"{path}?{query}" if query else path)
        cacheable = request.method in ("GET", "HEAD") and self._caching_enabled(behavior)
        if cacheable:
            cached = self.cache.get(dist_id, cache_key)
            if cached:
                response = Response(
                    cached.body if request.method == "GET" else b"",
                    status=cached.status,
                    headers=cached.headers,
                )
                return self._decorate(response, dist_id, hit=True)

        origin = self._origin(config, behavior.get("TargetOriginId"))
        if origin is None:
            return self._error(502, "Bad Gateway", "The cache behaviour has no origin.")
        status, headers, body = self._fetch(account_id, config, origin, request, path, query)
        status, headers, body, error_ttl = self._custom_error(
            account_id, config, origin, request, status, headers, body
        )

        if cacheable:
            ttl = error_ttl if error_ttl is not None else self._ttl(behavior, headers, status)
            if ttl > 0:
                self.cache.put(
                    dist_id,
                    cache_key,
                    CachedResponse(status, dict(headers), body, time.monotonic() + ttl),
                )
        response = Response(body if request.method != "HEAD" else b"", status=status)
        for name, value in headers.items():
            response.headers[name] = value
        return self._decorate(response, dist_id, hit=False)

    # ------------------------------------------------------------ behaviour

    @staticmethod
    def _behavior(config: dict[str, Any], path: str) -> dict[str, Any]:
        for behavior in _items(config.get("CacheBehaviors")):
            if _path_matches(behavior.get("PathPattern", ""), path):
                return behavior
        return config.get("DefaultCacheBehavior") or {}

    @staticmethod
    def _origin(config: dict[str, Any], origin_id: str | None) -> dict[str, Any] | None:
        for origin in _items(config.get("Origins")):
            if origin.get("Id") == origin_id:
                return origin
        return None

    @staticmethod
    def _forwards_query(behavior: dict[str, Any]) -> bool:
        forwarded = behavior.get("ForwardedValues")
        if forwarded:
            return bool(forwarded.get("QueryString"))
        # with a cache policy the query string is forwarded unless the policy says otherwise
        return True

    @staticmethod
    def _caching_enabled(behavior: dict[str, Any]) -> bool:
        if behavior.get("CachePolicyId") == CACHING_DISABLED_POLICY:
            return False
        if behavior.get("ForwardedValues") is not None:
            return (behavior.get("MaxTTL") or MAX_TTL) > 0 and (
                behavior.get("DefaultTTL", DEFAULT_TTL) > 0 or behavior.get("MinTTL", 0) > 0
            )
        return True

    @staticmethod
    def _ttl(behavior: dict[str, Any], headers: dict[str, str], status: int) -> int:
        if status >= 500:
            return 0
        if status >= 400:
            return ERROR_CACHING_TTL
        min_ttl = int(behavior.get("MinTTL") or 0)
        default_ttl = int(behavior.get("DefaultTTL", DEFAULT_TTL) or 0)
        max_ttl = int(behavior.get("MaxTTL", MAX_TTL) or 0)
        cache_control = next(
            (v for k, v in headers.items() if k.lower() == "cache-control"), ""
        ).lower()
        directives = dict(
            (part.split("=", 1) + [""])[:2] for part in cache_control.replace(" ", "").split(",")
        )
        if "no-store" in directives or "private" in directives or "no-cache" in directives:
            return min_ttl
        origin_ttl = directives.get("s-maxage") or directives.get("max-age")
        if origin_ttl and origin_ttl.isdigit():
            return max(min_ttl, min(int(origin_ttl), max_ttl))
        return max(min_ttl, min(default_ttl, max_ttl))

    # --------------------------------------------------------------- origins

    def _fetch(
        self,
        account_id: str,
        config: dict[str, Any],
        origin: dict[str, Any],
        request: Request,
        path: str,
        query: str,
    ) -> tuple[int, dict[str, str], bytes]:
        origin_path = origin.get("OriginPath") or ""
        domain = origin.get("DomainName", "")
        s3 = _S3_DOMAIN.match(domain)
        if s3 and "CustomOriginConfig" not in origin:
            if path == "/" and config.get("DefaultRootObject"):
                path = f"/{config['DefaultRootObject']}"
            return self._fetch_s3(account_id, s3.group("bucket"), f"{origin_path}{path}", request)
        return self._fetch_http(origin, request, f"{origin_path}{path}", query)

    def _fetch_s3(
        self, account_id: str, bucket: str, path: str, request: Request
    ) -> tuple[int, dict[str, str], bytes]:
        s3 = connect_to(aws_access_key_id=account_id, region_name="us-east-1").s3
        key = path.lstrip("/")
        if request.method not in ("GET", "HEAD"):
            return 403, {"Content-Type": "text/plain"}, b"Method not supported by an S3 origin"
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
        except s3.exceptions.NoSuchKey:
            return (
                404,
                {"Content-Type": "application/xml"},
                b"<Error><Code>NoSuchKey</Code></Error>",
            )
        except s3.exceptions.NoSuchBucket:
            return (
                404,
                {"Content-Type": "application/xml"},
                b"<Error><Code>NoSuchBucket</Code></Error>",
            )
        except Exception as e:
            code = getattr(e, "response", {}).get("ResponseMetadata", {}).get("HTTPStatusCode")
            return code or 502, {"Content-Type": "text/plain"}, str(e).encode()
        headers = {"Content-Type": obj.get("ContentType") or "binary/octet-stream"}
        if obj.get("ETag"):
            headers["ETag"] = obj["ETag"]
        if obj.get("CacheControl"):
            headers["Cache-Control"] = obj["CacheControl"]
        if obj.get("LastModified"):
            headers["Last-Modified"] = obj["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT")
        return 200, headers, obj["Body"].read()

    def _fetch_http(
        self, origin: dict[str, Any], request: Request, path: str, query: str
    ) -> tuple[int, dict[str, str], bytes]:
        custom = origin.get("CustomOriginConfig") or {}
        policy = custom.get("OriginProtocolPolicy", "match-viewer")
        if policy == "http-only":
            scheme = "http"
        elif policy == "https-only":
            scheme = "https"
        else:
            scheme = request.scheme
        port = custom.get("HTTPSPort", 443) if scheme == "https" else custom.get("HTTPPort", 80)
        domain = origin["DomainName"]
        url = f"{scheme}://{domain}:{port}{path}" + (f"?{query}" if query else "")

        headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
        headers["Host"] = domain
        headers["Via"] = "1.1 mocksy.cloudfront.net (CloudFront)"
        forwarded_for = request.headers.get("X-Forwarded-For")
        client_ip = request.remote_addr or ""
        headers["X-Forwarded-For"] = f"{forwarded_for}, {client_ip}" if forwarded_for else client_ip
        for header in _items(origin.get("CustomHeaders")):
            headers[header["HeaderName"]] = header["HeaderValue"]

        timeout = origin.get("ConnectionTimeout") or 10
        try:
            response = requests.request(
                request.method,
                url,
                headers=headers,
                data=request.get_data() or None,
                timeout=(timeout, 60),
                allow_redirects=False,
                verify=False,
            )
        except requests.RequestException as e:
            return (
                502,
                {"Content-Type": "text/plain"},
                f"Cannot reach the origin {url}: {e}".encode(),
            )
        response_headers = {
            k: v for k, v in response.headers.items() if k.lower() not in _HOP_BY_HOP
        }
        return response.status_code, response_headers, response.content

    def _custom_error(
        self,
        account_id: str,
        config: dict[str, Any],
        origin: dict[str, Any],
        request: Request,
        status: int,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[int, dict[str, str], bytes, int | None]:
        """Apply ``CustomErrorResponses``; the last value is the error caching TTL, if set."""
        for item in _items(config.get("CustomErrorResponses")):
            if int(item.get("ErrorCode", 0)) != status:
                continue
            ttl = item.get("ErrorCachingMinTTL")
            ttl = int(ttl) if ttl is not None else None
            page = item.get("ResponsePagePath")
            if not page:
                return status, headers, body, ttl
            page_status, page_headers, page_body = self._fetch(
                account_id, config, origin, request, page, ""
            )
            response_code = item.get("ResponseCode")
            new_status = int(response_code) if response_code else page_status
            return new_status, page_headers, page_body, ttl
        return status, headers, body, None

    # ------------------------------------------------------------- responses

    @staticmethod
    def _decorate(response: Response, distribution_id: str, hit: bool) -> Response:
        response.headers["X-Cache"] = "Hit from cloudfront" if hit else "Miss from cloudfront"
        response.headers["Via"] = f"1.1 {distribution_id.lower()}.cloudfront.net (CloudFront)"
        response.headers["X-Amz-Cf-Pop"] = "MOCKSY"
        response.headers["X-Amz-Cf-Id"] = uuid.uuid4().hex
        return response

    @staticmethod
    def _error(status: int, title: str, message: str) -> Response:
        body = (
            f"<html><head><title>{status} {title}</title></head><body>"
            f"<h1>{status} {title}</h1><p>{message}</p>"
            "<p>Generated by cloudfront (CloudFront) in mocksy</p></body></html>"
        )
        response = Response(body, status=status, mimetype="text/html")
        response.headers["X-Cache"] = "Error from cloudfront"
        return response


CLOUDFRONT_EDGE = CloudFrontEdge()
