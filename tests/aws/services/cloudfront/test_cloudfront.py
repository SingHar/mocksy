from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid


def _distribution_config(caller_reference: str) -> dict:
    return {
        "CallerReference": caller_reference,
        "Comment": "",
        "Enabled": True,
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": "api",
                    "DomainName": "api.example.com",
                    "CustomOriginConfig": {
                        "HTTPPort": 80,
                        "HTTPSPort": 443,
                        "OriginProtocolPolicy": "https-only",
                    },
                }
            ],
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": "api",
            "ViewerProtocolPolicy": "redirect-to-https",
            "MinTTL": 0,
            "ForwardedValues": {"QueryString": False, "Cookies": {"Forward": "none"}},
            "TrustedSigners": {"Enabled": False, "Quantity": 0},
        },
        "ViewerCertificate": {"CloudFrontDefaultCertificate": True},
    }


class TestCloudfront:
    @markers.aws.unknown
    def test_distribution_lifecycle(self, aws_client):
        created = aws_client.cloudfront.create_distribution(
            DistributionConfig=_distribution_config(short_uid())
        )
        distribution_id = created["Distribution"]["Id"]
        assert created["Distribution"]["DomainName"].endswith(".cloudfront.net")

        result = aws_client.cloudfront.get_distribution(Id=distribution_id)
        assert result["Distribution"]["Status"] == "Deployed"

        config = aws_client.cloudfront.get_distribution_config(Id=distribution_id)
        disabled = config["DistributionConfig"]
        disabled["Enabled"] = False
        updated = aws_client.cloudfront.update_distribution(
            Id=distribution_id, DistributionConfig=disabled, IfMatch=config["ETag"]
        )
        aws_client.cloudfront.delete_distribution(Id=distribution_id, IfMatch=updated["ETag"])

    @markers.aws.unknown
    def test_unset_values_are_not_returned(self, aws_client):
        """Unset policy IDs and SSLSupportMethod with the default certificate are not returned.

        Moto returns them, which makes OpenTofu and Terraform show a change on every plan.
        """
        created = aws_client.cloudfront.create_distribution(
            DistributionConfig=_distribution_config(short_uid())
        )
        distribution_id = created["Distribution"]["Id"]

        for config in (
            created["Distribution"]["DistributionConfig"],
            aws_client.cloudfront.get_distribution(Id=distribution_id)["Distribution"][
                "DistributionConfig"
            ],
            aws_client.cloudfront.get_distribution_config(Id=distribution_id)["DistributionConfig"],
        ):
            behavior = config["DefaultCacheBehavior"]
            for key in ("CachePolicyId", "OriginRequestPolicyId", "ResponseHeadersPolicyId"):
                assert behavior.get(key) in (None, ""), key
            assert "SSLSupportMethod" not in config["ViewerCertificate"]
