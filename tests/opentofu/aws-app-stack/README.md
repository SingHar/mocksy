# OpenTofu stack: ECS, RDS, ElastiCache, CloudFront

This stack checks that OpenTofu can create, read and destroy the resources of a
typical container application against mocksy:

- VPC with two subnets
- ECS cluster, Fargate task definition and service
- RDS PostgreSQL 18 instance with one read replica
- ElastiCache Valkey replication group with two nodes
- CloudFront distribution

## Run

1. Start mocksy on port 4566.
2. Run these commands in this folder:

```sh
tofu init
tofu apply -auto-approve
tofu plan -detailed-exitcode   # exit code 0: no changes after apply
tofu destroy -auto-approve
```

To use a different endpoint, set `-var endpoint=http://host:port`.

## Expected result

- `apply` creates 12 resources with no error.
- `plan` after `apply` shows no changes.
- `destroy` removes 12 resources with no error.

The full cycle takes about 6 minutes. Most of that time is the AWS provider's
own wait intervals for RDS, ElastiCache and CloudFront, not mocksy.
