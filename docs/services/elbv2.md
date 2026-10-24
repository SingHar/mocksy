# ELBv2 (Application Load Balancer) in mocksy

mocksy serves Application Load Balancers: listeners accept HTTP and HTTPS
requests, rules choose an action, and `forward` sends requests to healthy
targets. Moto stores the ELBv2 resources.

## Domain and ports

`DNSName` is `<name>-<10 digits>.<region>.elb.localhost.localstack.cloud`
(`internal-` in front for internal load balancers). The domain resolves to
127.0.0.1. A request reaches the load balancer in two ways:

| Way | Example | Listener used |
|---|---|---|
| mocksy's gateway, port 4566 | `curl -H "Host: $DNS" http://localhost:4566/` | `http`: the HTTP listener (port 80 first); `https`: the HTTPS listener (port 443 first) |
| The listener's own port | `curl http://$DNS/` | The listener on that port |

mocksy opens each listener's port (80, 443, 8080, ...) when it is free. One
server per port serves all load balancers, by `Host`, so several load balancers
can use port 80. When a port cannot be opened (in use, or below 1024 without
permission), mocksy logs it and only the gateway way works. When mocksy runs in
Docker, publish the ports, for example `-p 80:80 -p 443:443`.

HTTPS listeners use mocksy's certificate for `*.localhost.localstack.cloud`,
not the ACM certificate of the listener.

## Rules and actions

Rules are evaluated by priority, then the default rule. Within a condition one
value must match; all conditions of a rule must match.

| Condition | Match |
|---|---|
| `path-pattern` | Path (without query), `*` and `?` wildcards, case-sensitive |
| `host-header` | Host without port, wildcards, case-insensitive |
| `http-header` | Header value, wildcards, case-insensitive |
| `http-request-method` | Exact method |
| `query-string` | Key and value pairs, wildcards |
| `source-ip` | Client IP in a CIDR |

| Action | Effect |
|---|---|
| `forward` | One target group, or `ForwardConfig` with weights |
| `fixed-response` | Status, content type and body |
| `redirect` | 301 or 302 with `#{protocol}`, `#{host}`, `#{port}`, `#{path}`, `#{query}` |
| `authenticate-*` | Skipped with a warning; the next action is used |

Requests to targets keep `Host` and get `X-Forwarded-For`,
`X-Forwarded-Proto`, `X-Forwarded-Port` and `X-Amzn-Trace-Id`. Errors:

| Status | When |
|---|---|
| 503 | The target group has no registered targets |
| 502 | The target refused or reset the connection |
| 504 | The target did not answer within `idle_timeout.timeout_seconds` (default 60) |

## Targets and health checks

`ip` targets get requests in round robin. Health checks run for target groups
that a listener uses, with the group's path, port (`traffic-port` or a number),
protocol, interval, timeout, thresholds and matcher (`200`, `200-299`,
`200,302`). `DescribeTargetHealth` shows the state:

| State | Meaning |
|---|---|
| `initial` | Registered, not yet `HealthyThresholdCount` successful checks |
| `healthy` | Gets traffic |
| `unhealthy` | `UnhealthyThresholdCount` failed checks; no traffic |
| `unused` | No listener uses the target group |
| `unavailable` | Health checks are turned off for the group |

Only healthy targets get traffic. When no target is healthy, all registered
targets get traffic ("fail open"), as in AWS.

Limits: `instance` and `lambda` targets are not served. A target is identified
by its IP only (Moto's model): register each IP once per target group.

## ECS services

An ECS service with `loadBalancers` registers each task's IP and container port
in the target group when the task is RUNNING, and deregisters it when the task
stops. A task whose target becomes `unhealthy` is stopped with
`Task failed ELB health checks in (target-group ...)` and the service starts a
replacement, after `healthCheckGracePeriodSeconds`.

Targets are deregistered at once; the deregistration delay is not waited for.

## Metrics

Every `ELBV2_METRICS_INTERVAL` seconds mocksy publishes to CloudWatch,
namespace `AWS/ApplicationELB`, with the dimensions `LoadBalancer`
(`app/<name>/<id>`) and `TargetGroup` (`targetgroup/<name>/<id>`):

`RequestCount`, `TargetResponseTime`, `HTTPCode_Target_2XX_Count` (3XX, 4XX,
5XX), `HTTPCode_ELB_4XX_Count`, `HTTPCode_ELB_5XX_Count`,
`RequestCountPerTarget`, `HealthyHostCount`, `UnHealthyHostCount`.

With [Application Auto Scaling](application-autoscaling.md), use the predefined
metric `ALBRequestCountPerTarget` (with `ResourceLabel`), or step scaling on an
alarm on `TargetResponseTime` to scale on latency.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `ELBV2_RUN` | `1` | `0` records load balancers only. |
| `ELBV2_BIND_LISTENER_PORTS` | `1` | `0` serves load balancers on the gateway only. |
| `ELBV2_HEALTH_CHECKS` | `1` | `0` treats all registered targets as healthy. |
| `ELBV2_PUBLISH_METRICS` | `1` | `0` publishes no metrics. |
| `ELBV2_METRICS_INTERVAL` | `10` | Seconds between metric publications. |

## Not supported yet

- Network and Gateway Load Balancers (TCP, UDP, TLS listeners).
- Stickiness, slow start, authentication actions, mutual TLS, WebSockets and
  HTTP/2 to targets (responses are buffered).
- Access logs.
