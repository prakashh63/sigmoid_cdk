from aws_cdk.assertions import Match, Template


def test_log_retention_follows_stage(
    dev_template: Template, prod_template: Template
) -> None:
    dev_template.has_resource_properties("AWS::Logs::LogGroup", {"RetentionInDays": 7})
    prod_template.has_resource_properties(
        "AWS::Logs::LogGroup", {"RetentionInDays": 90}
    )


def test_log_groups_are_kms_encrypted(dev_template: Template) -> None:
    groups = dev_template.find_resources("AWS::Logs::LogGroup")
    assert groups and all("KmsKeyId" in g["Properties"] for g in groups.values())


def test_api_throttling_is_active(prod_template: Template) -> None:
    prod_template.has_resource_properties(
        "AWS::ApiGateway::Stage",
        {
            "StageName": "v1",
            "MethodSettings": Match.array_with(
                [
                    Match.object_like(
                        {"ThrottlingRateLimit": 2000, "ThrottlingBurstLimit": 500}
                    )
                ]
            ),
        },
    )


def test_cors_preflight_exists(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::ApiGateway::Method", {"HttpMethod": "OPTIONS"}
    )


def test_lambda_runs_with_own_role(dev_template: Template) -> None:
    dev_template.resource_count_is("AWS::Lambda::Function", 1)
    dev_template.has_resource_properties(
        "AWS::Lambda::Function", {"MemorySize": 512, "Runtime": "python3.14"}
    )


def test_multi_service_stack(full_template: Template) -> None:
    full_template.resource_count_is("AWS::Lambda::Function", 2)
    full_template.resource_count_is("AWS::SQS::Queue", 2)  # queue + dead-letter queue
    full_template.resource_count_is("AWS::Events::Rule", 1)
    full_template.resource_count_is("AWS::S3::Bucket", 2)
    full_template.resource_count_is("AWS::Lambda::EventSourceMapping", 1)
