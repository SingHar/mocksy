from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid


class TestRds:
    @markers.aws.unknown
    def test_postgres_instance_with_read_replica(self, aws_client, cleanups):
        primary_id = f"db-{short_uid()}"
        replica_id = f"{primary_id}-replica"

        aws_client.rds.create_db_instance(
            DBInstanceIdentifier=primary_id,
            Engine="postgres",
            EngineVersion="18",
            DBInstanceClass="db.t4g.micro",
            MasterUsername="app",
            MasterUserPassword="change-me-123",
            AllocatedStorage=20,
            BackupRetentionPeriod=1,
        )
        cleanups.append(
            lambda: aws_client.rds.delete_db_instance(
                DBInstanceIdentifier=primary_id, SkipFinalSnapshot=True
            )
        )
        aws_client.rds.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_id, SourceDBInstanceIdentifier=primary_id
        )
        cleanups.append(
            lambda: aws_client.rds.delete_db_instance(
                DBInstanceIdentifier=replica_id, SkipFinalSnapshot=True
            )
        )

        primary = aws_client.rds.describe_db_instances(DBInstanceIdentifier=primary_id)[
            "DBInstances"
        ][0]
        replica = aws_client.rds.describe_db_instances(DBInstanceIdentifier=replica_id)[
            "DBInstances"
        ][0]
        assert primary["Endpoint"]["Port"] == 5432
        assert replica["ReadReplicaSourceDBInstanceIdentifier"] == primary_id
        assert replica_id in primary["ReadReplicaDBInstanceIdentifiers"]

    @markers.aws.unknown
    def test_dbi_resource_ids_are_unique(self, aws_client, cleanups):
        """OpenTofu and Terraform read DB instances back by their DbiResourceId."""
        ids = [f"db-{short_uid()}" for _ in range(2)]
        for db_id in ids:
            aws_client.rds.create_db_instance(
                DBInstanceIdentifier=db_id,
                Engine="postgres",
                DBInstanceClass="db.t4g.micro",
                MasterUsername="app",
                MasterUserPassword="change-me-123",
                AllocatedStorage=20,
                BackupRetentionPeriod=1,
            )
            cleanups.append(
                lambda db_id=db_id: aws_client.rds.delete_db_instance(
                    DBInstanceIdentifier=db_id, SkipFinalSnapshot=True
                )
            )
        replica_id = f"{ids[0]}-replica"
        aws_client.rds.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_id, SourceDBInstanceIdentifier=ids[0]
        )
        cleanups.append(
            lambda: aws_client.rds.delete_db_instance(
                DBInstanceIdentifier=replica_id, SkipFinalSnapshot=True
            )
        )

        resource_ids = set()
        for db_id in [*ids, replica_id]:
            instance = aws_client.rds.describe_db_instances(DBInstanceIdentifier=db_id)[
                "DBInstances"
            ][0]
            resource_ids.add(instance["DbiResourceId"])
            found = aws_client.rds.describe_db_instances(
                Filters=[{"Name": "dbi-resource-id", "Values": [instance["DbiResourceId"]]}]
            )["DBInstances"]
            assert [i["DBInstanceIdentifier"] for i in found] == [db_id]
        assert len(resource_ids) == 3
