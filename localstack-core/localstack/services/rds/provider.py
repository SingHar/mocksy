"""RDS provider.

Operations are handled by Moto through the MotoFallbackDispatcher. PostgreSQL
instances run as Docker containers (see ``db_runner``).

Fixes on top of Moto:
- Moto gives every DB instance the same hard-coded ``DbiResourceId``. AWS gives
  each instance a unique one, and the AWS provider for OpenTofu/Terraform reads
  instances back by that ID, so it fails with "couldn't find resource". The
  provider gives each new instance a unique ID. Read replicas are copies of
  the primary in Moto, so they also get a new ID after they are created.
"""

import string

from moto.moto_api._internal import mock_random
from moto.rds.exceptions import RDSClientError
from moto.rds.models import DBInstance, RDSBackend, rds_backends

from localstack.aws.api.rds import RdsApi
from localstack.services.plugins import ServiceLifecycleHook
from localstack.services.rds.db_runner import DB_RUNNER
from localstack.state import StateVisitor
from localstack.utils.patch import patch

_RESOURCE_ID_CHARS = string.ascii_uppercase + string.digits


def _new_dbi_resource_id() -> str:
    """Return an ID in the AWS format: ``db-`` followed by 26 upper-case letters and digits."""
    return "db-" + "".join(mock_random.choice(_RESOURCE_ID_CHARS) for _ in range(26))


@patch(DBInstance.__init__)
def _db_instance_init(fn, self, *args, **kwargs):
    fn(self, *args, **kwargs)
    self.dbi_resource_id = _new_dbi_resource_id()


@patch(RDSBackend.create_db_instance_read_replica)
def _create_db_instance_read_replica(fn, self, db_kwargs):
    primary = self.find_db_from_id(db_kwargs["source_db_instance_identifier"])
    if primary.status != "available":
        # AWS accepts a read replica only of an available source instance
        raise RDSClientError(
            "InvalidDBInstanceState",
            f"DB Instance {primary.db_instance_identifier} is not in available state.",
        )
    replica = fn(self, db_kwargs)
    # Moto creates the replica with copy.copy(primary), so it has the primary's ID
    replica.dbi_resource_id = _new_dbi_resource_id()
    DB_RUNNER.create_replica(replica, primary)
    return replica


# Moto returns a fixed *.rds.amazonaws.com address; a running instance returns mocksy's host
_original_address = DBInstance.address


@property
def _address(self) -> str:
    return self.__dict__.get("_mocksy_address") or _original_address.fget(self)


DBInstance.address = _address


@patch(RDSBackend.create_db_instance)
def _create_db_instance(fn, self, db_kwargs):
    instance = fn(self, db_kwargs)
    DB_RUNNER.create(instance)
    return instance


@patch(RDSBackend.modify_db_instance)
def _modify_db_instance(fn, self, db_instance_identifier, db_kwargs):
    password = db_kwargs.get("master_user_password")
    instance = fn(self, db_instance_identifier, db_kwargs)
    if password:
        DB_RUNNER.change_master_password(instance, password)
    return instance


@patch(RDSBackend.reboot_db_instance)
def _reboot_db_instance(fn, self, db_instance_identifier, *args, **kwargs):
    instance = fn(self, db_instance_identifier, *args, **kwargs)
    DB_RUNNER.reboot(instance)
    return instance


@patch(RDSBackend.stop_db_instance)
def _stop_db_instance(fn, self, *args, **kwargs):
    instance = fn(self, *args, **kwargs)
    DB_RUNNER.stop(instance)
    return instance


@patch(RDSBackend.start_db_instance)
def _start_db_instance(fn, self, *args, **kwargs):
    instance = fn(self, *args, **kwargs)
    DB_RUNNER.start(instance)
    return instance


@patch(RDSBackend.delete_db_instance)
def _delete_db_instance(fn, self, db_instance_identifier, *args, **kwargs):
    instance = self.databases.get(db_instance_identifier)
    if instance is not None and getattr(instance, "replicas", None):
        # AWS promotes the read replicas of a deleted source to standalone instances.
        # Moto keeps the link, and a later DeleteDBInstance of a replica then fails.
        for replica_id in list(instance.replicas):
            replica = self.databases.get(replica_id)
            if replica is not None:
                replica.is_replica = False
                replica.source_db_instance_identifier = None
        instance.replicas = []
    instance = fn(self, db_instance_identifier, *args, **kwargs)
    DB_RUNNER.delete(instance)
    return instance


class RdsProvider(RdsApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(rds_backends)

    def on_before_stop(self):
        DB_RUNNER.shutdown()

    def on_before_state_reset(self):
        DB_RUNNER.shutdown()
