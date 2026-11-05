"""RDS PostgreSQL instances run as Docker containers (issue #2, phase 2).

These tests start real PostgreSQL containers from ``RDS_POSTGRES_IMAGE``
(default ``postgres:{major}``).
"""

import json

import pg8000.native
import pytest

from localstack.testing.pytest import markers
from localstack.utils.docker_utils import DOCKER_CLIENT
from localstack.utils.strings import short_uid
from localstack.utils.sync import retry

pytestmark = [
    markers.requires_docker,
    pytest.mark.skipif(not DOCKER_CLIENT.has_docker(), reason="needs Docker"),
]

ENGINE_VERSION = "16"


def _wait_available(aws_client, identifier: str) -> dict:
    def _check():
        instance = aws_client.rds.describe_db_instances(DBInstanceIdentifier=identifier)[
            "DBInstances"
        ][0]
        assert instance["DBInstanceStatus"] in ("available", "failed")
        return instance

    instance = retry(_check, retries=180, sleep=1)
    assert instance["DBInstanceStatus"] == "available"
    return instance


def _connect(instance: dict, user: str, password: str, database: str = "postgres"):
    # the endpoint host is localhost.localstack.cloud; connect to it on this machine
    return pg8000.native.Connection(
        user=user,
        password=password,
        host="127.0.0.1",
        port=instance["Endpoint"]["Port"],
        database=database,
        timeout=10,
    )


@pytest.fixture
def create_instance(aws_client):
    created = []

    def _create(**kwargs) -> str:
        identifier = kwargs.setdefault("DBInstanceIdentifier", f"db-{short_uid()}")
        kwargs.setdefault("Engine", "postgres")
        kwargs.setdefault("EngineVersion", ENGINE_VERSION)
        kwargs.setdefault("DBInstanceClass", "db.t4g.micro")
        kwargs.setdefault("MasterUsername", "app")
        kwargs.setdefault("AllocatedStorage", 20)
        kwargs.setdefault("BackupRetentionPeriod", 1)
        aws_client.rds.create_db_instance(**kwargs)
        created.append(identifier)
        return identifier

    yield _create

    for identifier in reversed(created):
        try:
            aws_client.rds.delete_db_instance(
                DBInstanceIdentifier=identifier, SkipFinalSnapshot=True
            )
        except Exception:
            pass


class TestRdsContainers:
    @markers.aws.only_localstack
    def test_instance_accepts_connections(self, aws_client, create_instance):
        identifier = create_instance(MasterUserPassword="initial-pw-123", DBName="appdb")
        assert (
            aws_client.rds.describe_db_instances(DBInstanceIdentifier=identifier)["DBInstances"][0][
                "DBInstanceStatus"
            ]
            == "creating"
        )

        instance = _wait_available(aws_client, identifier)
        assert instance["Endpoint"]["Address"] == "localhost.localstack.cloud"

        conn = _connect(instance, "app", "initial-pw-123", "appdb")
        assert conn.run("SELECT current_database(), current_user") == [["appdb", "app"]]
        conn.close()

        # a new master password applies to the database
        aws_client.rds.modify_db_instance(
            DBInstanceIdentifier=identifier,
            MasterUserPassword="changed-pw-456",
            ApplyImmediately=True,
        )
        conn = _connect(instance, "app", "changed-pw-456")
        assert conn.run("SELECT 1") == [[1]]
        conn.close()
        with pytest.raises(pg8000.native.DatabaseError):
            _connect(instance, "app", "initial-pw-123")

    @markers.aws.only_localstack
    def test_managed_master_password(self, aws_client, create_instance):
        identifier = create_instance(ManageMasterUserPassword=True)
        instance = _wait_available(aws_client, identifier)

        secret = json.loads(
            aws_client.secretsmanager.get_secret_value(
                SecretId=instance["MasterUserSecret"]["SecretArn"]
            )["SecretString"]
        )
        assert secret["username"] == "app"
        conn = _connect(instance, "app", secret["password"])
        assert conn.run("SELECT current_user") == [["app"]]
        conn.close()

    @markers.aws.only_localstack
    def test_read_replica_streams_from_primary(self, aws_client, create_instance):
        identifier = create_instance(MasterUserPassword="replica-pw-123", DBName="appdb")
        primary = _wait_available(aws_client, identifier)
        replica_id = f"{identifier}-replica"
        aws_client.rds.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_id, SourceDBInstanceIdentifier=identifier
        )
        try:
            replica = _wait_available(aws_client, replica_id)
            assert replica["Endpoint"]["Port"] != primary["Endpoint"]["Port"]

            conn = _connect(primary, "app", "replica-pw-123", "appdb")
            conn.run("CREATE TABLE items (value int)")
            conn.run("INSERT INTO items VALUES (42)")
            conn.close()

            def _replicated():
                c = _connect(replica, "app", "replica-pw-123", "appdb")
                try:
                    assert c.run("SELECT value FROM items") == [[42]]
                    assert c.run("SELECT pg_is_in_recovery()") == [[True]]
                finally:
                    c.close()

            retry(_replicated, retries=20, sleep=1)
        finally:
            aws_client.rds.delete_db_instance(
                DBInstanceIdentifier=replica_id, SkipFinalSnapshot=True
            )

    @markers.aws.only_localstack
    def test_stop_start_and_delete(self, aws_client, create_instance):
        identifier = create_instance(MasterUserPassword="stop-pw-123")
        instance = _wait_available(aws_client, identifier)
        arn = instance["DBInstanceArn"]

        aws_client.rds.stop_db_instance(DBInstanceIdentifier=identifier)
        with pytest.raises((pg8000.native.InterfaceError, OSError)):
            _connect(instance, "app", "stop-pw-123")

        aws_client.rds.start_db_instance(DBInstanceIdentifier=identifier)
        instance = _wait_available(aws_client, identifier)

        def _connects():
            _connect(instance, "app", "stop-pw-123").close()

        retry(_connects, retries=30, sleep=1)

        aws_client.rds.delete_db_instance(DBInstanceIdentifier=identifier, SkipFinalSnapshot=True)
        assert not DOCKER_CLIENT.list_containers(filter=f"label=mocksy.resource.arn={arn}")

    @markers.aws.only_localstack
    def test_replica_needs_available_source(self, aws_client, create_instance):
        identifier = create_instance(MasterUserPassword="source-pw-123")
        with pytest.raises(aws_client.rds.exceptions.ClientError) as e:
            aws_client.rds.create_db_instance_read_replica(
                DBInstanceIdentifier=f"{identifier}-replica", SourceDBInstanceIdentifier=identifier
            )
        assert e.value.response["Error"]["Code"] == "InvalidDBInstanceState"
        _wait_available(aws_client, identifier)

    @markers.aws.only_localstack
    def test_delete_source_promotes_replica(self, aws_client, create_instance):
        identifier = create_instance(MasterUserPassword="promote-pw-123")
        _wait_available(aws_client, identifier)
        replica_id = f"{identifier}-replica"
        aws_client.rds.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_id, SourceDBInstanceIdentifier=identifier
        )
        replica_arn = _wait_available(aws_client, replica_id)["DBInstanceArn"]

        aws_client.rds.delete_db_instance(DBInstanceIdentifier=identifier, SkipFinalSnapshot=True)
        replica = aws_client.rds.describe_db_instances(DBInstanceIdentifier=replica_id)[
            "DBInstances"
        ][0]
        assert not replica.get("ReadReplicaSourceDBInstanceIdentifier")

        aws_client.rds.delete_db_instance(DBInstanceIdentifier=replica_id, SkipFinalSnapshot=True)
        assert not DOCKER_CLIENT.list_containers(filter=f"label=mocksy.resource.arn={replica_arn}")
