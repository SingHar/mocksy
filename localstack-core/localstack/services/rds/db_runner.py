"""Runs RDS PostgreSQL instances as Docker containers (issue #2, phase 2).

Moto stores the RDS resources. This module adds a real database:

- CreateDBInstance (engine ``postgres``) starts a ``postgres:<major>`` container.
  The instance is ``creating`` until the server accepts connections, then
  ``available``. The endpoint is ``<LOCALSTACK_HOST host>:<port>`` (see
  ``container_resources``).
- ``MasterUsername``, ``MasterUserPassword`` and ``DBName`` are applied. With
  ``ManageMasterUserPassword``, a random password is stored in the managed
  Secrets Manager secret, as in AWS.
- CreateDBInstanceReadReplica starts a second container with streaming
  replication from the primary.
- StopDBInstance, StartDBInstance, RebootDBInstance, DeleteDBInstance and a
  new master password in ModifyDBInstance act on the container.

Other engines, and all engines when Docker is not available or
``RDS_RUN_CONTAINERS=0``, are recorded only, as in phase 1.
"""

from __future__ import annotations

import json
import logging
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from localstack import config
from localstack.aws.connect import connect_to
from localstack.services.container_resources import (
    LABEL_RESOURCE,
    ContainerResource,
    ContainerResourceError,
    container_name,
    docker_available,
)

LOG = logging.getLogger(__name__)

POSTGRES_PORT = 5432
SUPPORTED_ENGINES = ("postgres",)

# The replica container clones the primary with pg_basebackup, then runs as a standby.
# Environment: PRIMARY_HOST, PRIMARY_PORT, REPL_USER, PGPASSWORD (and PGDATA from the image).
_REPLICA_SCRIPT = r"""
set -e
until pg_isready -q -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$REPL_USER"; do sleep 1; done
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  mkdir -p "$PGDATA" /var/run/postgresql
  chown postgres:postgres "$PGDATA" /var/run/postgresql
  chmod 700 "$PGDATA"
  gosu postgres pg_basebackup -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$REPL_USER" \
    -D "$PGDATA" -R -X stream
fi
exec gosu postgres postgres -c listen_addresses='*'
"""

# Lets the master user connect for replication, with the same method as normal connections.
_ALLOW_REPLICATION_SCRIPT = r"""
set -e
hba="$PGDATA/pg_hba.conf"
if ! grep -qE '^host[[:space:]]+replication[[:space:]]+all[[:space:]]+all' "$hba"; then
  method=$(awk '$1=="host" && $2=="all" && $3=="all" && $4=="all" {print $5; exit}' "$hba")
  echo "host replication all all ${method:-scram-sha-256}" >> "$hba"
fi
"""


def _major_version(version: str) -> str:
    """``18.4`` -> ``18``; ``9.6.24`` -> ``9.6`` (before PostgreSQL 10 the major has two parts)."""
    parts = version.split(".")
    if parts and parts[0].isdigit() and int(parts[0]) < 10 and len(parts) > 1:
        return f"{parts[0]}.{parts[1]}"
    return parts[0]


class DbInstanceRunner:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        # instance ARN -> container
        self._resources: dict[str, ContainerResource] = {}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rds-instance")
        self._docker: bool | None = None

    def handles(self, instance: Any) -> bool:
        if not config.RDS_RUN_CONTAINERS or instance.engine not in SUPPORTED_ENGINES:
            return False
        if self._docker is None:
            self._docker = docker_available()
            if not self._docker:
                LOG.warning("Docker is not available: RDS instances are recorded only")
        return self._docker

    def resource(self, instance: Any) -> ContainerResource | None:
        with self._lock:
            return self._resources.get(instance.arn)

    # -------------------------------------------------------------- create

    def create(self, instance: Any) -> None:
        if not self.handles(instance):
            return
        if not instance.engine_version or instance.engine_version == "9.3.3":
            # Moto's default is PostgreSQL 9.3.3; use a supported version instead
            instance.engine_version = config.RDS_POSTGRES_DEFAULT_VERSION
        instance.status = "creating"
        self._executor.submit(self._run, instance, self._start_primary)

    def create_replica(self, replica: Any, primary: Any) -> None:
        if not self.handles(replica):
            return
        # Moto copies the primary, including its endpoint; the replica gets its own
        replica.__dict__.pop("_mocksy_address", None)
        replica.__dict__.pop("_mocksy_resource", None)
        replica.__dict__.pop("_mocksy_deleted", None)
        replica.port = POSTGRES_PORT
        replica.status = "creating"
        self._executor.submit(self._run, replica, lambda r: self._start_replica(r, primary))

    def _run(self, instance: Any, start) -> None:
        try:
            start(instance)
            if self._deleted(instance):
                return
            instance.status = "available"
        except Exception as e:
            if self._deleted(instance):
                return
            LOG.warning("RDS instance %s cannot start: %s", instance.db_instance_identifier, e)
            instance.status = "failed"
        finally:
            # DeleteDBInstance can arrive while the container is starting. It then finds
            # no container to remove, so the starting thread removes it here.
            if self._deleted(instance) or instance.status == "failed":
                self._remove(instance)
                resource = instance.__dict__.get("_mocksy_resource")
                if resource is not None:
                    resource.stop(remove=True)

    @staticmethod
    def _deleted(instance: Any) -> bool:
        return instance.__dict__.get("_mocksy_deleted", False)

    def _new_resource(self, instance: Any) -> ContainerResource:
        if self._deleted(instance):
            raise ContainerResourceError("The instance was deleted while it was created")
        image = config.RDS_POSTGRES_IMAGE.format(major=_major_version(instance.engine_version))
        resource = ContainerResource(
            name=container_name(
                "rds", instance.account_id, instance.region, instance.db_instance_identifier
            ),
            image=image,
            internal_port=POSTGRES_PORT,
        )
        with self._lock:
            self._resources[instance.arn] = resource
        instance._mocksy_resource = resource
        return resource

    def _start_primary(self, instance: Any) -> None:
        password = self._master_password(instance)
        resource = self._new_resource(instance)
        resource.start(
            env={
                "POSTGRES_USER": instance.master_username,
                "POSTGRES_PASSWORD": password,
                "POSTGRES_DB": instance.db_name or "postgres",
            },
            labels={LABEL_RESOURCE: instance.arn},
        )
        self._check_not_deleted(instance)
        self._wait_ready(resource, instance.master_username, password, instance)
        resource.exec(["bash", "-c", _ALLOW_REPLICATION_SCRIPT])
        self._sql(resource, instance.master_username, password, "SELECT pg_reload_conf()")
        self._publish_endpoint(instance, resource)

    def _start_replica(self, replica: Any, primary: Any) -> None:
        source = self.resource(primary)
        if source is None:
            raise ContainerResourceError(
                f"The source instance {primary.db_instance_identifier} has no running database"
            )
        password = self._master_password(primary)
        resource = self._new_resource(replica)
        resource.start(
            env={
                "PRIMARY_HOST": source.network_ip,
                "PRIMARY_PORT": str(POSTGRES_PORT),
                "REPL_USER": primary.master_username,
                "PGPASSWORD": password,
            },
            # Docker takes a single word as entrypoint; the script is the command
            entrypoint="bash",
            command=["-c", _REPLICA_SCRIPT],
            labels={LABEL_RESOURCE: replica.arn},
        )
        self._check_not_deleted(replica)
        self._wait_ready(resource, primary.master_username, password, replica)
        self._publish_endpoint(replica, resource)

    def _publish_endpoint(self, instance: Any, resource: ContainerResource) -> None:
        instance._mocksy_address = resource.endpoint_host
        instance.port = resource.external_port

    # ------------------------------------------------------------ password

    def _master_password(self, instance: Any) -> str:
        """Return the master password; for a managed password, create it and store it."""
        secret = getattr(instance, "master_user_secret", None)
        if not secret:
            # Moto's master_user_password property raises (AWS never returns the password)
            return instance.__dict__.get("_master_user_password") or ""
        clients = connect_to(aws_access_key_id=instance.account_id, region_name=instance.region)
        arn = secret.secret.arn
        current = json.loads(clients.secretsmanager.get_secret_value(SecretId=arn)["SecretString"])
        if current.get("username") == instance.master_username and getattr(
            instance, "_mocksy_password_set", False
        ):
            return current["password"]
        password = secrets.token_urlsafe(24)
        clients.secretsmanager.put_secret_value(
            SecretId=arn,
            SecretString=json.dumps({"username": instance.master_username, "password": password}),
        )
        instance._mocksy_password_set = True
        secret._status = "active"
        return password

    def change_master_password(self, instance: Any, password: str) -> None:
        """Apply a new master password (ModifyDBInstance with MasterUserPassword)."""
        resource = self.resource(instance)
        if not resource:
            return
        user = instance.master_username
        escaped = password.replace("'", "''")
        # the local socket uses "trust" in the postgres image, so the old password is not needed
        self._sql(
            resource, user, "", f"ALTER ROLE \"{user}\" WITH PASSWORD '{escaped}'", local=True
        )

    # ------------------------------------------------------------ lifecycle

    def stop(self, instance: Any) -> None:
        resource = self.resource(instance)
        if resource:
            resource.stop(remove=False)

    def start(self, instance: Any) -> None:
        resource = self.resource(instance)
        if not resource:
            return
        resource.resume()
        self._publish_endpoint(instance, resource)

    def reboot(self, instance: Any) -> None:
        resource = self.resource(instance)
        if resource:
            resource.restart()

    def delete(self, instance: Any) -> None:
        instance._mocksy_deleted = True
        self._remove(instance)

    def _remove(self, instance: Any) -> None:
        with self._lock:
            resource = self._resources.pop(instance.arn, None)
        if resource:
            resource.stop(remove=True)

    def shutdown(self) -> None:
        with self._lock:
            resources = list(self._resources.values())
            self._resources.clear()
        for resource in resources:
            resource.stop(remove=True)

    # ------------------------------------------------------------ helpers

    def _check_not_deleted(self, instance: Any) -> None:
        if self._deleted(instance):
            raise ContainerResourceError("The instance was deleted while it was created")

    def _wait_ready(
        self, resource: ContainerResource, user: str, password: str, instance: Any
    ) -> None:
        def _ready() -> bool:
            self._check_not_deleted(instance)
            # TCP on 127.0.0.1 is only answered by the final server, not by the
            # temporary server that the image entrypoint runs during setup
            self._sql(resource, user, password, "SELECT 1")
            return True

        resource.wait_until(_ready, timeout=config.RDS_START_TIMEOUT, what="database ready")

    def _sql(
        self,
        resource: ContainerResource,
        user: str,
        password: str,
        sql: str,
        local: bool = False,
    ) -> str:
        command = ["psql", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", "postgres", "-tAc", sql]
        if not local:
            command[1:1] = ["-h", "127.0.0.1"]
        return resource.exec(command, env={"PGPASSWORD": password})


DB_RUNNER = DbInstanceRunner()
