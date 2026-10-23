"""RDS provider.

Phase 1: operations are handled by Moto through the MotoFallbackDispatcher.
Instances are recorded but no database server runs yet (see issue #2, phase 2).

Fixes on top of Moto:
- Moto gives every DB instance the same hard-coded ``DbiResourceId``. AWS gives
  each instance a unique one, and the AWS provider for OpenTofu/Terraform reads
  instances back by that ID, so it fails with "couldn't find resource". The
  provider gives each new instance a unique ID. Read replicas are copies of
  the primary in Moto, so they also get a new ID after they are created.
"""

import string

from moto.moto_api._internal import mock_random
from moto.rds.models import DBInstance, RDSBackend, rds_backends

from localstack.aws.api.rds import RdsApi
from localstack.services.plugins import ServiceLifecycleHook
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
    replica = fn(self, db_kwargs)
    # Moto creates the replica with copy.copy(primary), so it has the primary's ID
    replica.dbi_resource_id = _new_dbi_resource_id()
    return replica


class RdsProvider(RdsApi, ServiceLifecycleHook):
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(rds_backends)
