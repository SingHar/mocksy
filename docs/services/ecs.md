# ECS in mocksy

mocksy runs ECS tasks as Docker containers. Moto stores the ECS resources;
mocksy starts and stops the containers.

## What runs

| AWS action | Effect in mocksy |
|---|---|
| RunTask, StartTask | Starts one container for each container definition. |
| StopTask | Stops the containers in the background. The task shows `desiredStatus=STOPPED` at once and `lastStatus=STOPPED` when the containers have stopped. |
| CreateService, UpdateService | Keeps `desiredCount` tasks running. Stopped tasks are replaced. A new task definition replaces the old tasks. |
| DeleteService | Stops the service's tasks. |

When an essential container exits, the task stops with
`stopCode=EssentialContainerExited` and the container's `exitCode`.

When a task cannot start (image not found, secret not found, log group not
found), it stops with `stopCode=TaskFailedToStart` and an AWS-style
`stoppedReason`. A service then waits before it tries again: 5 s, 10 s, 20 s,
up to 5 minutes.

## Container configuration

- `environment` and container overrides are set.
- `secrets` are read when the container starts, from Secrets Manager
  (`arn:...:secret:name[:json-key:stage:version]`) or SSM Parameter Store
  (name or ARN).
- `command`, `entryPoint`, `workingDirectory`, `user` and `memory` are used.
- With the `awslogs` log driver, container output goes to CloudWatch Logs.
  The stream name is `<awslogs-stream-prefix>/<container>/<task-id>`. The log
  group must exist, unless `awslogs-create-group` is `true`.
- Each container gets `AWS_ENDPOINT_URL`, `AWS_REGION` and test credentials, so
  AWS SDKs in the container call mocksy.

## Network

Containers join the mocksy Docker network. The task's `privateIPv4Address`
is the IP of its first container on that network.

Differences from AWS Fargate:

- Each container has its own IP. In AWS, the containers of a task share one
  network interface.
- Ports are not published on the host. On Linux you can reach the container IP
  from the host. On macOS and Windows, use another container on the same
  network.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `ECS_RUN_CONTAINERS` | `1` | `0` records tasks only and runs no containers. |
| `ECS_DOCKER_NETWORK` | mocksy network | Docker network for task containers. |
| `ECS_REMOVE_CONTAINERS` | `1` | `0` keeps stopped containers for debugging. |
| `ECS_DISABLE_AWS_ENDPOINT_URL` | `0` | `1` does not set `AWS_ENDPOINT_URL` in containers. |
| `ECS_MONITOR_INTERVAL` | `2` | Seconds between checks of containers and service task counts. |

When Docker is not available, mocksy records tasks only and logs a warning.

## Not supported yet

- Container `dependsOn`, health checks and `stopTimeout` (stop waits 10 s).
- Load balancer registration (ELBv2 is not in mocksy).
- Task metadata endpoint and task IAM role credentials.
