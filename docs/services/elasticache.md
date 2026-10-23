# ElastiCache in mocksy

mocksy runs ElastiCache nodes as Docker containers. Moto stores the
ElastiCache resources; mocksy runs Valkey, Redis or Memcached.

## What runs

| AWS action | Effect in mocksy |
|---|---|
| CreateReplicationGroup (cluster mode disabled) | One container per member cluster. The first is the primary; the others replicate from it. The group is `creating` until all nodes answer, then `available`. |
| CreateCacheCluster (not in a replication group) | One container. |
| DeleteReplicationGroup, DeleteCacheCluster | Removes the containers. A delete while the group is being created also removes them. |

| Engine | Image (default) |
|---|---|
| `valkey` | `valkey/valkey:{major}` |
| `redis` | `redis:{major}` |
| `memcached` | `memcached:{minor}` (for example `1.6`) |

`AuthToken` sets the server password. Replicas use it to connect to the primary.

## Endpoints

| Field | Value |
|---|---|
| `PrimaryEndpoint`, `ReaderEndpoint` | `localhost.localstack.cloud` and the group's port (`Port` of the request, default 6379) |
| Each member's `ReadEndpoint` | `localhost.localstack.cloud` and a port of mocksy's external range (4510-4559); the primary member uses the group's port |
| Cache cluster `CacheNodes[].Endpoint` | `localhost.localstack.cloud` and a port of the external range |

Why the group's port: Terraform/OpenTofu treat the port of
`aws_elasticache_replication_group` as an input. Any other port would make every
plan replace the group.

Consequences:

- The reader endpoint reaches the primary, because one address and port can
  reach only one node. Reads work, but they are not spread over the replicas.
  To read from a replica, use that member's `ReadEndpoint`.
- Only one replication group can listen on 6379. When the port is in use (by
  another group, or by a Redis server on your machine), the group uses a port of
  the external range and mocksy logs a warning. Terraform/OpenTofu then show a
  change on the next plan. Give each group its own `port` to avoid this.
- When mocksy runs in Docker, publish the group's port, for example
  `-p 6379:6379`. The external range is published by default.

## TLS

With `TransitEncryptionEnabled`, mocksy accepts TLS on the endpoint ports with
its certificate for `localhost.localstack.cloud`, and forwards plain TCP to the
server. Any image works. Clients that check certificates need to trust
mocksy's certificate, or turn off verification for local use.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `ELASTICACHE_RUN_CONTAINERS` | `1` | `0` records clusters only. |
| `ELASTICACHE_VALKEY_IMAGE` | `valkey/valkey:{major}` | Image for Valkey. `{major}` and `{minor}` come from the engine version (`8.1` gives `8` and `8.1`). |
| `ELASTICACHE_REDIS_IMAGE` | `redis:{major}` | Image for Redis. |
| `ELASTICACHE_MEMCACHED_IMAGE` | `memcached:{minor}` | Image for Memcached. |
| `ELASTICACHE_START_TIMEOUT` | `60` | Seconds to wait for a node. After that the status is `create-failed`. |

When Docker is not available, mocksy records clusters only and logs a warning.

## Not supported yet

- Cluster mode (sharding, `NumNodeGroups > 1`): recorded only.
- Changes after creation: ModifyReplicationGroup (new auth token, more
  replicas), failover, snapshots, user groups (RBAC).
- Data is lost when mocksy stops.
