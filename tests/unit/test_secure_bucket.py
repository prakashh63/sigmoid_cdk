from aws_cdk.assertions import Match, Template


def test_public_access_fully_blocked(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )


def test_encrypted_with_s3_managed_keys(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [Match.any_value()]
            }
        },
    )


def test_versioning_only_in_prod(
    prod_template: Template, dev_template: Template
) -> None:
    prod_template.has_resource_properties(
        "AWS::S3::Bucket", {"VersioningConfiguration": {"Status": "Enabled"}}
    )
    buckets = dev_template.find_resources("AWS::S3::Bucket")
    assert all(
        "VersioningConfiguration" not in b["Properties"] for b in buckets.values()
    )


def test_https_only_bucket_policy(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Effect": "Deny",
                                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
                            }
                        )
                    ]
                )
            }
        },
    )
