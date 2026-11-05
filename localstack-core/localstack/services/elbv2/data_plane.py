"""Routes HTTP traffic through Application Load Balancers (issue #14, phase 2).

Moto stores the ELBv2 resources. This module serves them:

- **Ingress.** A load balancer's ``DNSName`` is
  ``<name>-<id>.<region>.elb.<LOCALSTACK_HOST host>``. Requests reach it on
  mocksy's gateway (port 4566; ``http`` uses the HTTP listener, ``https`` the
  HTTPS listener) and, when the port is free, on each listener's own port
  (80, 443, ...). One server per port serves every load balancer by ``Host``.
- **Rules** are evaluated by priority, then the default rule. Conditions:
  ``path-pattern``, ``host-header``, ``http-header``, ``http-request-method``,
  ``query-string``, ``source-ip`` (values in a condition: any; conditions: all).
- **Actions:** ``forward`` (one target group, or weighted target groups),
  ``fixed-response`` and ``redirect`` (``#{protocol}``, ``#{host}``, ``#{port}``,
  ``#{path}``, ``#{query}``).
- **Targets** (``ip``) get requests in round robin. Only healthy targets get
  traffic; when none is healthy, all registered targets do ("fail open"), as in
  AWS. Without registered targets the answer is 503.
- **Health checks** run per target group with its path, port, protocol,
  interval, timeout, thresholds and matcher. ``DescribeTargetHealth`` shows the
  result. Tasks of ECS services that fail them are replaced.
- **Metrics:** ``AWS/ApplicationELB`` ``RequestCount``, ``TargetResponseTime``,
  ``HTTPCode_Target_<n>XX_Count``, ``HTTPCode_ELB_<n>XX_Count``,
  ``RequestCountPerTarget``, ``HealthyHostCount`` and ``UnHealthyHostCount``
  go to CloudWatch.
"""

from __future__ import annotations

import fnmatch
import ipaddress
import logging
import random
import ssl
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl

import requests
import urllib3
from rolo import Request
from werkzeug.serving import make_server
from werkzeug.wrappers import Request as WerkzeugRequest

from localstack import config
from localstack.aws.connect import connect_to
from localstack.http import Response
from localstack.utils.urls import localstack_host

LOG = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HOST_PATTERN = (
    "<regex('[a-z0-9-]+'):lb_name>.<regex('[a-z0-9-]+'):lb_region>.elb.<regex('.*'):server>"
)

_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


def load_balancer_domain(name: str, lb_id: str, region: str) -> str:
    """``<name>-<10 digits>.<region>.elb.<host>``, like ``name-1234567890.region.elb.amazonaws.com``."""
    digits = str(
        int(lb_id, 16) if all(c in "0123456789abcdef" for c in lb_id) else abs(hash(lb_id))
    )
    return f"{name.lower()}-{digits[-10:].rjust(10, '0')}.{region}.elb.{localstack_host().host}"


def _values(condition: dict[str, Any], config_key: str) -> list:
    """Values of a rule condition, from ``Values`` or the ``<Type>Config`` structure."""
    values = (condition.get(config_key) or {}).get("Values") or condition.get("Values") or []
    if isinstance(values, dict):  # query protocol shapes: {"member": [...]}
        values = values.get("member") or values.get("item") or list(values.values())
    return values if isinstance(values, list) else [values]


def _wildcard(pattern: str, value: str, case_sensitive: bool) -> bool:
    if not case_sensitive:
        pattern, value = pattern.lower(), value.lower()
    return fnmatch.fnmatchcase(value, pattern)


def _items(value: Any) -> list:
    if not value:
        return []
    if isinstance(value, dict):
        value = value.get("member") or value.get("Items") or value.get("item") or []
    return value if isinstance(value, list) else [value]


# ---------------------------------------------------------------- health


@dataclass
class TargetState:
    target_id: str
    port: int
    state: str = "initial"
    reason: str | None = "Elb.RegistrationInProgress"
    description: str | None = "Target registration is in progress"
    successes: int = 0
    failures: int = 0
    next_check: float = 0.0
    unhealthy_since: float | None = None


@dataclass
class _Counters:
    requests: int = 0
    response_time_sum: float = 0.0
    response_time_count: int = 0
    response_time_min: float = float("inf")
    response_time_max: float = 0.0
    target_codes: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    elb_codes: dict[str, int] = field(default_factory=lambda: defaultdict(int))


class Elbv2DataPlane:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        # target group ARN -> "id:port" -> state
        self._health: dict[str, dict[str, TargetState]] = {}
        self._round_robin: dict[str, int] = defaultdict(int)
        # (account, region, load balancer ARN, target group ARN or "") -> counters
        self._counters: dict[tuple[str, str, str, str], _Counters] = {}
        self._servers: dict[int, tuple[str, Any, threading.Thread]] = {}
        self._failed_ports: set[int] = set()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._last_metrics = time.monotonic()

    # ------------------------------------------------------------- lookup

    @staticmethod
    def _backends():
        from moto.elbv2.models import elbv2_backends

        for account_id, regions in list(elbv2_backends.items()):
            for region, backend in list(regions.items()):
                yield account_id, region, backend

    def _find_by_host(self, host: str):
        host = host.split(":", 1)[0].lower().rstrip(".")
        for account_id, region, backend in self._backends():
            for lb in list(backend.load_balancers.values()):
                if (lb.dns_name or "").lower() == host:
                    return account_id, region, backend, lb
        return None

    @staticmethod
    def _listener_for(lb: Any, port: int | None, scheme: str):
        listeners = [x for x in lb.listeners.values() if x.protocol in ("HTTP", "HTTPS")]
        if port is not None:
            return next((x for x in listeners if int(x.port) == port), None)
        # gateway (port 4566): the listener of the request's scheme, standard port first
        wanted = "HTTPS" if scheme == "https" else "HTTP"
        standard = 443 if wanted == "HTTPS" else 80
        candidates = sorted(
            (x for x in listeners if x.protocol == wanted),
            key=lambda x: (int(x.port) != standard, int(x.port)),
        )
        return candidates[0] if candidates else None

    # ------------------------------------------------------------- serving

    def __call__(self, request: Request, **kwargs) -> Response:
        """Gateway route (port 4566)."""
        return self.handle(request, port=None)

    def handle(self, request: Request, port: int | None) -> Response:
        found = self._find_by_host(request.host or "")
        if not found:
            return self._error(404, "Not Found")
        account_id, region, backend, lb = found
        scheme = request.scheme
        listener = self._listener_for(lb, port, scheme)
        if listener is None:
            return self._error(404, "Not Found")
        if (listener.protocol == "HTTPS") != (scheme == "https"):
            # plain HTTP on an HTTPS listener (or the other way round): AWS drops the connection
            return self._error(400, "Bad Request")
        self._ensure_started()

        started = time.monotonic()
        response, target_group_arn = self._dispatch(
            account_id, region, backend, lb, listener, request
        )
        elapsed = time.monotonic() - started
        self._count(account_id, region, lb.arn, target_group_arn, response, elapsed)
        return response

    def _dispatch(self, account_id, region, backend, lb, listener, request) -> tuple[Response, str]:
        rule = self._match_rule(listener, request)
        if rule is None:
            return self._error(503, "Service Temporarily Unavailable"), ""
        for action in sorted(rule.actions, key=lambda a: int(_action(a).get("Order") or 0)):
            data = _action(action)
            kind = data.get("Type")
            if kind == "forward":
                target_group_arn = self._choose_target_group(data)
                target_group = backend.target_groups.get(target_group_arn)
                if target_group is None:
                    return self._error(503, "Service Temporarily Unavailable"), ""
                return self._forward(lb, listener, target_group, request), target_group_arn
            if kind == "fixed-response":
                return self._fixed(data), ""
            if kind == "redirect":
                return self._redirect(data, listener, request), ""
            if kind and kind.startswith("authenticate-"):
                LOG.warning("ELBv2 %s actions are not supported; the next action is used", kind)
                continue
        return self._error(503, "Service Temporarily Unavailable"), ""

    # --------------------------------------------------------------- rules

    def _match_rule(self, listener: Any, request: Request):
        rules = list(listener.rules.values())
        ordered = sorted(
            (r for r in rules if not getattr(r, "is_default", False) and r.priority != "default"),
            key=lambda r: int(r.priority),
        )
        default = [r for r in rules if getattr(r, "is_default", False) or r.priority == "default"]
        for rule in ordered:
            if self._conditions_match(rule.conditions or [], request):
                return rule
        return default[0] if default else None

    def _conditions_match(self, conditions: list[dict[str, Any]], request: Request) -> bool:
        host = (request.host or "").split(":", 1)[0]
        for condition in _items(conditions):
            name = condition.get("Field")
            if name == "path-pattern":
                values = _values(condition, "PathPatternConfig")
                if not any(_wildcard(v, request.path, True) for v in values):
                    return False
            elif name == "host-header":
                values = _values(condition, "HostHeaderConfig")
                if not any(_wildcard(v, host, False) for v in values):
                    return False
            elif name == "http-request-method":
                values = _values(condition, "HttpRequestMethodConfig")
                if request.method not in values:
                    return False
            elif name == "http-header":
                header_config = condition.get("HttpHeaderConfig") or {}
                header = request.headers.get(header_config.get("HttpHeaderName") or "", "")
                values = _values(condition, "HttpHeaderConfig")
                if not any(_wildcard(v, header, False) for v in values):
                    return False
            elif name == "query-string":
                pairs = parse_qsl(request.query_string.decode(), keep_blank_values=True)
                values = _values(condition, "QueryStringConfig")
                if not any(
                    any(
                        (v.get("Key") is None or _wildcard(v["Key"], k, False))
                        and _wildcard(v.get("Value", "*"), val, False)
                        for k, val in pairs
                    )
                    for v in values
                ):
                    return False
            elif name == "source-ip":
                values = _values(condition, "SourceIpConfig")
                try:
                    client = ipaddress.ip_address(request.remote_addr or "0.0.0.0")
                    if not any(client in ipaddress.ip_network(v, strict=False) for v in values):
                        return False
                except ValueError:
                    return False
        return True

    # ------------------------------------------------------------- actions

    @staticmethod
    def _choose_target_group(data: dict[str, Any]) -> str:
        groups = _items((data.get("ForwardConfig") or {}).get("TargetGroups"))
        weighted = [(g["TargetGroupArn"], int(g.get("Weight", 1) or 0)) for g in groups]
        weighted = [(arn, w) for arn, w in weighted if w > 0]
        if weighted:
            arns, weights = zip(*weighted, strict=True)
            return random.choices(arns, weights=weights)[0]
        return data.get("TargetGroupArn") or (groups[0]["TargetGroupArn"] if groups else "")

    @staticmethod
    def _fixed(data: dict[str, Any]) -> Response:
        cfg = data.get("FixedResponseConfig") or {}
        response = Response(
            cfg.get("MessageBody") or "",
            status=int(cfg.get("StatusCode") or 200),
            content_type=cfg.get("ContentType") or "text/plain",
        )
        response.headers["Server"] = "awselb/2.0"
        return response

    @staticmethod
    def _redirect(data: dict[str, Any], listener: Any, request: Request) -> Response:
        cfg = data.get("RedirectConfig") or {}
        values = {
            "protocol": "https" if listener.protocol == "HTTPS" else "http",
            "host": (request.host or "").split(":", 1)[0],
            "port": str(listener.port),
            "path": request.path.lstrip("/"),
            "query": request.query_string.decode(),
        }

        def fill(template: str) -> str:
            for key, value in values.items():
                template = template.replace("#{" + key + "}", value)
            return template

        protocol = fill(cfg.get("Protocol") or "#{protocol}").lower()
        host = fill(cfg.get("Host") or "#{host}")
        port = fill(cfg.get("Port") or "#{port}")
        path = fill(cfg.get("Path") or "/#{path}")
        query = fill(cfg.get("Query") or "#{query}")
        default_port = {"http": "80", "https": "443"}.get(protocol)
        netloc = host if port == default_port else f"{host}:{port}"
        location = f"{protocol}://{netloc}{path}" + (f"?{query}" if query else "")
        status = 301 if (cfg.get("StatusCode") or "HTTP_301") == "HTTP_301" else 302
        response = Response(status=status, headers={"Location": location})
        response.headers["Server"] = "awselb/2.0"
        return response

    def _forward(self, lb: Any, listener: Any, target_group: Any, request: Request) -> Response:
        targets = list(target_group.targets.values())
        if not targets:
            return self._error(503, "Service Temporarily Unavailable")
        with self._lock:
            states = self._health.get(target_group.arn, {})
            healthy = [
                t
                for t in targets
                if states.get(f"{t['Id']}:{t.get('Port')}", TargetState("", 0)).state
                in ("healthy", "unavailable")
            ]
            pool = healthy or targets  # fail open
            index = self._round_robin[target_group.arn] % len(pool)
            self._round_robin[target_group.arn] += 1
        target = pool[index]
        scheme = "https" if (target_group.protocol or "HTTP") == "HTTPS" else "http"
        url = f"{scheme}://{target['Id']}:{target.get('Port') or target_group.port}{request.full_path.rstrip('?')}"

        headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
        client_ip = request.remote_addr or ""
        forwarded_for = request.headers.get("X-Forwarded-For")
        headers["X-Forwarded-For"] = f"{forwarded_for}, {client_ip}" if forwarded_for else client_ip
        headers["X-Forwarded-Proto"] = request.scheme
        headers["X-Forwarded-Port"] = str(listener.port)
        if "X-Amzn-Trace-Id" not in request.headers:
            headers["X-Amzn-Trace-Id"] = f"Root=1-{int(time.time()):08x}-{uuid.uuid4().hex[:24]}"

        timeout = float((lb.attrs or {}).get("idle_timeout.timeout_seconds") or 60)
        try:
            upstream = requests.request(
                request.method,
                url,
                headers=headers,
                data=request.get_data() or None,
                timeout=(5, timeout),
                allow_redirects=False,
                verify=False,
            )
        except requests.Timeout:
            return self._error(504, "Gateway Time-out")
        except requests.RequestException as e:
            LOG.debug("ELBv2 target %s failed: %s", url, e)
            return self._error(502, "Bad Gateway")
        response = Response(upstream.content, status=upstream.status_code)
        for name, value in upstream.headers.items():
            if name.lower() not in _HOP_BY_HOP and name.lower() != "content-encoding":
                response.headers[name] = value
        response._mocksy_from_target = True
        return response

    @staticmethod
    def _error(status: int, title: str) -> Response:
        body = (
            f"<html>\r\n<head><title>{status} {title}</title></head>\r\n<body>\r\n"
            f"<center><h1>{status} {title}</h1></center>\r\n</body>\r\n</html>\r\n"
        )
        response = Response(body, status=status, mimetype="text/html")
        response.headers["Server"] = "awselb/2.0"
        return response

    # ------------------------------------------------------------ registry

    def target_health(self, target_group: Any, target_id: str, port: Any) -> TargetState | None:
        with self._lock:
            return self._health.get(target_group.arn, {}).get(f"{target_id}:{port}")

    def target_groups_in_use(self, backend: Any) -> set[str]:
        return self._target_groups_in_use(backend)

    def forget_target_group(self, arn: str) -> None:
        with self._lock:
            self._health.pop(arn, None)
            self._round_robin.pop(arn, None)

    # ---------------------------------------------------------------- loop

    def _ensure_started(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="elbv2", daemon=True)
            self._thread.start()

    def ensure_started(self) -> None:
        if config.ELBV2_RUN:
            self._ensure_started()

    def shutdown(self) -> None:
        self._stop.set()
        with self._lock:
            servers = list(self._servers.values())
            self._servers.clear()
            self._health.clear()
            self._counters.clear()
        for _, server, _ in servers:
            try:
                server.shutdown()
            except Exception:
                pass

    def _run(self) -> None:
        while not self._stop.wait(0.5):
            try:
                if config.ELBV2_BIND_LISTENER_PORTS:
                    self._reconcile_servers()
                self._run_health_checks()
                if (
                    config.ELBV2_PUBLISH_METRICS
                    and time.monotonic() - self._last_metrics >= config.ELBV2_METRICS_INTERVAL
                ):
                    self._last_metrics = time.monotonic()
                    self._publish_metrics()
            except Exception:
                LOG.exception("Error in the ELBv2 loop")

    # ---------------------------------------------------- listener servers

    def _reconcile_servers(self) -> None:
        wanted: dict[int, str] = {}
        for _, _, backend in self._backends():
            for lb in list(backend.load_balancers.values()):
                for listener in list(lb.listeners.values()):
                    if listener.protocol in ("HTTP", "HTTPS"):
                        wanted.setdefault(int(listener.port), listener.protocol)
        gateway_ports = {hp.port for hp in config.GATEWAY_LISTEN}
        for port, protocol in wanted.items():
            if port in self._servers or port in self._failed_ports or port in gateway_ports:
                continue
            self._start_server(port, protocol)
        for port in [p for p in self._servers if p not in wanted]:
            _, server, _ = self._servers.pop(port)
            server.shutdown()
        self._failed_ports &= set(wanted)

    def _start_server(self, port: int, protocol: str) -> None:
        def app(environ, start_response):
            request = WerkzeugRequest(environ)
            return self.handle(request, port=port)(environ, start_response)

        ssl_context = None
        if protocol == "HTTPS":
            from localstack.utils.ssl import create_ssl_cert

            _, cert_file, key_file = create_ssl_cert()
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_file, key_file)
        host = config.GATEWAY_LISTEN[0].host if config.GATEWAY_LISTEN else "0.0.0.0"
        try:
            server = make_server(host, port, app, threaded=True, ssl_context=ssl_context)
        except OSError as e:
            self._failed_ports.add(port)
            LOG.info(
                "ELBv2 listener port %s is not available (%s); use mocksy's port %s instead",
                port,
                e,
                config.GATEWAY_LISTEN[0].port,
            )
            return
        thread = threading.Thread(target=server.serve_forever, name=f"elbv2-{port}", daemon=True)
        thread.start()
        self._servers[port] = (protocol, server, thread)
        LOG.info("ELBv2 listens on port %s (%s)", port, protocol)

    # ------------------------------------------------------- health checks

    def _run_health_checks(self) -> None:
        now = time.monotonic()
        for account_id, region, backend in self._backends():
            in_use = self._target_groups_in_use(backend)
            for target_group in list(backend.target_groups.values()):
                if target_group.arn not in in_use:
                    continue
                self._check_group(account_id, region, target_group, now)

    @staticmethod
    def _target_groups_in_use(backend: Any) -> set[str]:
        used = set()
        for lb in list(backend.load_balancers.values()):
            for listener in list(lb.listeners.values()):
                for rule in list(listener.rules.values()):
                    for action in rule.actions or []:
                        data = _action(action)
                        if data.get("TargetGroupArn"):
                            used.add(data["TargetGroupArn"])
                        for group in _items((data.get("ForwardConfig") or {}).get("TargetGroups")):
                            used.add(group.get("TargetGroupArn"))
        return used

    def _check_group(self, account_id: str, region: str, target_group: Any, now: float) -> None:
        with self._lock:
            states = self._health.setdefault(target_group.arn, {})
            registered = {
                f"{t['Id']}:{t.get('Port') or target_group.port}": t
                for t in target_group.targets.values()
            }
            for key in [k for k in states if k not in registered]:
                del states[key]
            for key, target in registered.items():
                if key not in states:
                    states[key] = TargetState(
                        target["Id"], int(target.get("Port") or target_group.port)
                    )
            due = [s for s in states.values() if s.next_check <= now]

        if not config.ELBV2_HEALTH_CHECKS:
            for state in due:
                state.state, state.reason, state.description = "healthy", None, None
                state.next_check = now + 5
            return
        enabled = str(getattr(target_group, "health_check_enabled", True)).lower() != "false"
        interval = float(target_group.health_check_interval_seconds or 30)
        for state in due:
            state.next_check = now + interval
            if not enabled:
                state.state, state.reason = "unavailable", "Target.HealthCheckDisabled"
                state.description = "Health checks are disabled"
                continue
            ok, reason = self._probe(target_group, state)
            self._record_probe(account_id, region, target_group, state, ok, reason)

    @staticmethod
    def _probe(target_group: Any, state: TargetState) -> tuple[bool, str]:
        port = target_group.health_check_port
        port = state.port if not port or port == "traffic-port" else int(port)
        protocol = (target_group.health_check_protocol or "HTTP").upper()
        path = target_group.health_check_path or "/"
        url = f"{'https' if protocol == 'HTTPS' else 'http'}://{state.target_id}:{port}{path}"
        timeout = float(target_group.health_check_timeout_seconds or 5)
        try:
            response = requests.get(url, timeout=timeout, verify=False, allow_redirects=False)
        except requests.Timeout:
            return False, "Target.Timeout"
        except requests.RequestException:
            return False, "Target.FailedHealthChecks"
        matcher = (getattr(target_group, "matcher", None) or {}).get("HttpCode") or "200"
        return _code_matches(response.status_code, matcher), "Target.ResponseCodeMismatch"

    def _record_probe(self, account_id, region, target_group, state, ok: bool, reason: str) -> None:
        healthy_threshold = int(target_group.healthy_threshold_count or 5)
        unhealthy_threshold = int(target_group.unhealthy_threshold_count or 2)
        if ok:
            state.successes, state.failures = state.successes + 1, 0
            if state.state != "healthy" and state.successes >= healthy_threshold:
                state.state, state.reason, state.description = "healthy", None, None
                state.unhealthy_since = None
        else:
            state.failures, state.successes = state.failures + 1, 0
            if state.state != "unhealthy" and state.failures >= unhealthy_threshold:
                state.state, state.reason = "unhealthy", reason
                state.description = {
                    "Target.Timeout": "Request timed out",
                    "Target.ResponseCodeMismatch": "Health checks failed with these codes",
                }.get(reason, "Health checks failed")
                state.unhealthy_since = time.monotonic()
                self._replace_ecs_task(account_id, region, target_group, state)

    @staticmethod
    def _replace_ecs_task(account_id, region, target_group, state: TargetState) -> None:
        """ECS replaces a service task that fails the load balancer health checks."""
        try:
            from localstack.services.ecs.task_runner import TASK_RUNNER
        except ImportError:
            return
        TASK_RUNNER.stop_unhealthy_target(account_id, region, target_group.arn, state.target_id)

    # ------------------------------------------------------------- metrics

    def _count(self, account_id, region, lb_arn, target_group_arn, response, elapsed) -> None:
        """Count a request for the load balancer, and for the target group when it was forwarded."""
        code = f"{response.status_code // 100}XX"
        keys = [(account_id, region, lb_arn, "")]
        if target_group_arn:
            keys.append((account_id, region, lb_arn, target_group_arn))
        from_target = getattr(response, "_mocksy_from_target", False)
        with self._lock:
            for key in keys:
                c = self._counters.setdefault(key, _Counters())
                c.requests += 1
                if from_target:
                    c.target_codes[code] += 1
                    c.response_time_sum += elapsed
                    c.response_time_count += 1
                    c.response_time_min = min(c.response_time_min, elapsed)
                    c.response_time_max = max(c.response_time_max, elapsed)
                elif response.status_code >= 400:
                    c.elb_codes[code] += 1

    def _publish_metrics(self) -> None:
        with self._lock:
            counters, self._counters = self._counters, {}
            health = {arn: dict(states) for arn, states in self._health.items()}
        by_target: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for (account_id, region, lb_arn, tg_arn), c in counters.items():
            dims = [{"Name": "LoadBalancer", "Value": lb_arn.split(":loadbalancer/", 1)[-1]}]
            if tg_arn:
                dims = [{"Name": "TargetGroup", "Value": tg_arn.split(":", 5)[-1]}, *dims]
            data = by_target[(account_id, region)]
            data.append(
                {
                    "MetricName": "RequestCount",
                    "Dimensions": dims,
                    "Value": c.requests,
                    "Unit": "Count",
                }
            )
            if c.response_time_count:
                data.append(
                    {
                        "MetricName": "TargetResponseTime",
                        "Dimensions": dims,
                        "StatisticValues": {
                            "SampleCount": c.response_time_count,
                            "Sum": c.response_time_sum,
                            "Minimum": c.response_time_min,
                            "Maximum": c.response_time_max,
                        },
                        "Unit": "Seconds",
                    }
                )
            for code, n in c.target_codes.items():
                data.append(
                    {
                        "MetricName": f"HTTPCode_Target_{code}_Count",
                        "Dimensions": dims,
                        "Value": n,
                        "Unit": "Count",
                    }
                )
            for code, n in c.elb_codes.items():
                data.append(
                    {
                        "MetricName": f"HTTPCode_ELB_{code}_Count",
                        "Dimensions": dims,
                        "Value": n,
                        "Unit": "Count",
                    }
                )
            if tg_arn:
                healthy = sum(1 for s in health.get(tg_arn, {}).values() if s.state == "healthy")
                tg_dims = [{"Name": "TargetGroup", "Value": tg_arn.split(":", 5)[-1]}]
                data.append(
                    {
                        "MetricName": "RequestCountPerTarget",
                        "Dimensions": tg_dims,
                        "Value": c.requests / max(healthy, 1),
                        "Unit": "None",
                    }
                )
        # healthy and unhealthy host counts, also without traffic
        for account_id, region, backend in self._backends():
            for lb in list(backend.load_balancers.values()):
                lb_dim = {"Name": "LoadBalancer", "Value": lb.arn.split(":loadbalancer/", 1)[-1]}
                for tg_arn in self._target_groups_in_use(backend):
                    states = health.get(tg_arn, {}).values()
                    dims = [{"Name": "TargetGroup", "Value": tg_arn.split(":", 5)[-1]}, lb_dim]
                    by_target[(account_id, region)].extend(
                        [
                            {
                                "MetricName": "HealthyHostCount",
                                "Dimensions": dims,
                                "Value": sum(1 for s in states if s.state == "healthy"),
                                "Unit": "Count",
                            },
                            {
                                "MetricName": "UnHealthyHostCount",
                                "Dimensions": dims,
                                "Value": sum(1 for s in states if s.state == "unhealthy"),
                                "Unit": "Count",
                            },
                        ]
                    )
        for (account_id, region), data in by_target.items():
            if not data:
                continue
            cloudwatch = connect_to(aws_access_key_id=account_id, region_name=region).cloudwatch
            for start in range(0, len(data), 20):
                try:
                    cloudwatch.put_metric_data(
                        Namespace="AWS/ApplicationELB", MetricData=data[start : start + 20]
                    )
                except Exception as e:
                    LOG.debug("Cannot publish ELBv2 metrics: %s", e)


def _action(action: Any) -> dict[str, Any]:
    return getattr(action, "data", None) or (action if isinstance(action, dict) else {})


def _code_matches(code: int, matcher: str) -> bool:
    for part in str(matcher).split(","):
        part = part.strip()
        if "-" in part:
            low, high = part.split("-", 1)
            if int(low) <= code <= int(high):
                return True
        elif part and int(part) == code:
            return True
    return False


DATA_PLANE = Elbv2DataPlane()
