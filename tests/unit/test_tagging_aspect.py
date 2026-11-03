from aws_cdk.assertions import Template


def test_every_taggable_resource_has_standard_tags(dev_template: Template) -> None:
    expected = {
        "Environment": "dev",
        "Owner": "frontend-devs",
        "CostCenter": "cc-100",
        "ManagedBy": "sigmoid-cdk",
    }
    for resource_type in (
        "AWS::S3::Bucket",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::KMS::Key",
    ):
        resources = dev_template.find_resources(resource_type)
        assert resources, resource_type
        for resource in resources.values():
            tags = {t["Key"]: t["Value"] for t in resource["Properties"]["Tags"]}
            assert expected.items() <= tags.items(), resource_type
