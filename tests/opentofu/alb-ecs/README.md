# OpenTofu stack: Application Load Balancer in front of ECS

This stack checks that OpenTofu can create, read and destroy an Application
Load Balancer with an ECS service behind it, and that traffic flows:

- VPC with two subnets and a security group
- Application Load Balancer, `ip` target group with health checks
- HTTP listener: `/api/*` and `/health` go to the target group, other paths get
  a fixed 404
- ECS Fargate service with 2 tasks and a `load_balancer` block

## Run

1. Start mocksy on port 4566, with Docker available.
2. Run these commands in this folder:

```sh
tofu init
tofu apply -auto-approve
DNS=$(tofu output -raw alb_dns_name)
curl -H "Host: $DNS" http://localhost:4566/api/items   # through mocksy's gateway
curl http://$DNS/api/items                              # through the listener port (80)
tofu plan -detailed-exitcode                            # exit code 0: no changes
tofu destroy -auto-approve
```

Port 80 is used only when it is free and mocksy may bind it (see
`docs/services/elbv2.md`). Set `-var image=...` when `python:3.13-alpine` cannot
be pulled.

## Expected result

- `apply` creates 11 resources; both tasks become `healthy` in the target group.
- Requests to `/api/*` alternate between the two tasks; `/other` returns 404.
- `plan` after `apply` shows no changes.
- `destroy` removes 11 resources and no task containers remain.
