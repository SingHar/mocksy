# RDS in mocksy

mocksy runs RDS PostgreSQL instances as Docker containers. Moto stores the RDS
resources; mocksy runs the database.

## What runs

| AWS action | Effect in mocksy |
|---|---|
| CreateDBInstance (`Engine=postgres`) | Starts a `postgres:<major>` container. Status is `creating` until the database accepts connections, then `available`. |
| CreateDBInstanceReadReplica | Starts a second container that copies the primary (`pg_basebackup`) and then streams changes from it. The replica is read-only. |
| ModifyDBInstance with `MasterUserPassword` | Changes the password in the database. |
| StopDBInstance, StartDBInstance | Stops and starts the container. Data is kept. |
| RebootDBInstance | Restarts the container. |
| DeleteDBInstance | Removes the container and its data. |

`MasterUsername`, `MasterUserPassword` and `DBName` are applied. With
`ManageMasterUserPassword`, mocksy creates a random password and stores
`{"username", "password"}` in the managed Secrets Manager secret
(`MasterUserSecret.SecretArn`), as AWS does.

Without `EngineVersion`, the instance uses `RDS_POSTGRES_DEFAULT_VERSION`.

## Endpoint

`Endpoint.Address` is `localhost.localstack.cloud` (the `LOCALSTACK_HOST` host)
and `Endpoint.Port` is a port from mocksy's external service port range
(`EXTERNAL_SERVICE_PORTS_START`..`EXTERNAL_SERVICE_PORTS_END`, default
4510-4559). mocksy forwards that port to the database container.

`localhost.localstack.cloud` resolves to 127.0.0.1. From the host, connect to
it directly. From other containers, use mocksy's DNS server, or the mocksy
container's address with the same port.

Each instance and each replica uses one port of the range, so the range limits
the number of instances (50 by default, shared with other services).

Do not set `port` on `aws_db_instance` in Terraform/OpenTofu. mocksy returns its
own port, so a configured port shows as a change on every plan.

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `RDS_RUN_CONTAINERS` | `1` | `0` records instances only. |
| `RDS_POSTGRES_IMAGE` | `postgres:{major}` | Image for PostgreSQL. `{major}` is the major engine version, for example `18`. Use it for a registry mirror or a custom image. The image must work like the official Debian-based image: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` and `PGDATA`, with `bash`, `gosu` and the PostgreSQL client tools. The Alpine variants have no `gosu`, so read replicas do not start with them. |
| `RDS_POSTGRES_DEFAULT_VERSION` | `18.4` | Engine version when the request has none. It is not guaranteed to match the AWS default. |
| `RDS_START_TIMEOUT` | `180` | Seconds to wait for the database. After that the instance status is `failed`. |

When Docker is not available, mocksy records instances only and logs a warning.

## Not supported yet

- Engines other than `postgres` (MySQL, MariaDB, Aurora) are recorded only.
- Snapshots, restore, point-in-time recovery and parameter groups do not
  change the database.
- Promoting a replica (`PromoteReadReplica`).
- TLS and IAM database authentication.
- Data is lost when mocksy stops, unless persistence is added later.
