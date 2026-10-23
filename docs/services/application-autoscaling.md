# Application Auto Scaling in mocksy

mocksy applies Application Auto Scaling policies to ECS services. Moto stores
the scalable targets and policies; mocksy evaluates them and changes the
service's `desiredCount`. With ECS containers on (see [ECS](ecs.md)), the
number of running task containers follows.

## What is evaluated

Every `APPLICATION_AUTOSCALING_INTERVAL` seconds, for each scalable target with
`ServiceNamespace=ecs` and `ScalableDimension=ecs:service:DesiredCount`:

| Policy type | How the new capacity is found |
|---|---|
| Target tracking, predefined `ECSServiceAverageCPUUtilization` or `ECSServiceAverageMemoryUtilization` | Reads `AWS/ECS` `CPUUtilization` or `MemoryUtilization` (dimensions `ClusterName`, `ServiceName`) from CloudWatch. `ceil(current × value / target)`. |
| Target tracking, `CustomizedMetricSpecification` | Reads the metric (namespace, name, dimensions, statistic) from CloudWatch, for example a queue depth that your app publishes. Same formula. |
| Step scaling | Acts when a CloudWatch alarm that has the policy ARN in `AlarmActions` is in `ALARM`. The step adjustment is chosen by `metric value − alarm threshold`. `ChangeInCapacity`, `PercentChangeInCapacity` (with `MinAdjustmentMagnitude`) and `ExactCapacity` are supported. |

Then:

- The result stays between `MinCapacity` and `MaxCapacity`.
- `DisableScaleIn` stops target tracking from scaling in.
- `ScaleOutCooldown`, `ScaleInCooldown` (target tracking) and `Cooldown` (step
  scaling) are respected. Without a value, the cooldown is 300 s.
- `SuspendedState` (`DynamicScalingInSuspended`, `DynamicScalingOutSuspended`)
  stops scaling in that direction.
- Each change is a scaling activity in DescribeScalingActivities.

The value used is the latest datapoint of the last three periods
(`APPLICATION_AUTOSCALING_METRIC_PERIOD`). Without datapoints, nothing changes.

## ECS metrics

mocksy publishes `AWS/ECS` `CPUUtilization` and `MemoryUtilization` for ECS
services with running task containers, as AWS does. The values come from
`docker stats`: CPU as a percentage of the task's `cpu` units, memory as a
percentage of the task's `memory`.

## Example: scale workers on queue depth

Publish the queue depth from your app (or a small job) to CloudWatch:

```python
cloudwatch.put_metric_data(
    Namespace="App/Queue",
    MetricData=[{
        "MetricName": "Depth",
        "Dimensions": [{"Name": "Queue", "Value": "default"}],
        "Value": depth,
    }],
)
```

Then use a target tracking policy with that metric, as in
`tests/opentofu/aws-app-stack/main.tf`. With `target_value = 10`, 35 waiting
jobs and 1 task, the service goes to 4 tasks (or `max_capacity`).

## Differences from AWS

- AWS waits for several datapoints over some minutes before it scales (the
  target tracking alarms). mocksy acts at the next evaluation, so local tests
  run fast. Use the cooldowns to slow it down.
- The alarms that AWS creates for target tracking policies are not created.
- `ALBRequestCountPerTarget`, other predefined metrics, metric math,
  predictive scaling and scheduled actions are not evaluated.
- Only ECS services are scaled. Other namespaces are recorded only.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `APPLICATION_AUTOSCALING_RUN` | `1` | `0` records targets and policies only. |
| `APPLICATION_AUTOSCALING_INTERVAL` | `15` | Seconds between evaluations. |
| `APPLICATION_AUTOSCALING_METRIC_PERIOD` | `60` | CloudWatch period in seconds for reading metrics. Use `1` with high-resolution metrics (`StorageResolution=1`) for fast local tests. |
