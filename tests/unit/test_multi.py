"""Stacks with several Lambdas, buckets and topics."""

import json

from typing import Any

from collections.abc import Callable, Mapping

from aws_cdk.assertions import Match, Template

Build = Callable[..., Template]


def multi(lambda_dir: str) -> dict[str, Any]:
    def fn(name: str, **extra: Any) -> dict[str, Any]:
        return {"function_name": name, "entry_point_dir": lambda_dir, **extra}

    return {
        "buckets": {
            "website": {"bucket_name": "demo-web-bucket", "cdn_default": True},
            "assets": {"bucket_name": "demo-assets-bucket", "cdn_path": "/assets/*"},
            "uploads": {"bucket_name": "demo-uploads-bucket"},
        },
        "topics": {"orders": {"topic_name": "orders-topic"}},
        "lambdas": {
            "users": fn("users-fn", bucket_access={"uploads": "read_write"}),
            "reports": fn(
                "reports-fn",
                bucket_access={"uploads": "read"},
                triggers={"schedule": {"expression": "rate(1 day)"}},
            ),
            "order-worker": fn("worker-fn", triggers={"sns": ["orders"]}),
            "audit": fn("audit-fn", triggers={"sns": ["orders"]}),
        },
        "api_gateway": {
            "routes": [
                {"path": "/api/users", "function": "users"},
                {"path": "/api/reports", "function": "reports"},
            ]
        },
    }


def test_resource_counts(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    t.resource_count_is("AWS::Lambda::Function", 4)
    t.resource_count_is("AWS::S3::Bucket", 3)
    t.resource_count_is("AWS::SNS::Topic", 1)
    t.resource_count_is("AWS::ApiGateway::RestApi", 1)
    t.resource_count_is("AWS::CloudFront::Distribution", 1)
    # one shared key, not one per Lambda
    t.resource_count_is("AWS::KMS::Key", 1)
    # 4 function log groups + 1 API access log group
    t.resource_count_is("AWS::Logs::LogGroup", 5)
    # 4 function roles + the API Gateway CloudWatch role
    t.resource_count_is("AWS::IAM::Role", 5)


def test_every_log_group_uses_the_shared_key(build: Build, lambda_dir: str) -> None:
    build(**multi(lambda_dir)).resource_properties_count_is(
        "AWS::Logs::LogGroup", {"KmsKeyId": Match.any_value()}, 5
    )


def test_cdn_has_one_behavior_per_bucket_path_and_the_api(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    t.resource_count_is("AWS::CloudFront::OriginAccessControl", 2)
    for pattern in ("/assets/*", "/api/*"):
        t.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": {
                    "CacheBehaviors": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "PathPattern": pattern,
                                    "ViewerProtocolPolicy": "redirect-to-https",
                                }
                            )
                        ]
                    )
                }
            },
        )
    distribution = next(iter(t.find_resources("AWS::CloudFront::Distribution").values()))
    assert len(distribution["Properties"]["DistributionConfig"]["Origins"]) == 3


def test_private_bucket_is_not_behind_cdn(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    t.resource_properties_count_is(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
        3,
    )
    # only the two CDN buckets get a CloudFront bucket policy statement
    cloudfront_policies = [
        policy
        for policy in t.find_resources("AWS::S3::BucketPolicy").values()
        if "cloudfront.amazonaws.com" in json.dumps(policy)
    ]
    assert len(cloudfront_policies) == 2


def test_bucket_env_vars_only_where_granted(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    functions = {
        res["Properties"]["FunctionName"]: res["Properties"]
        for res in t.find_resources("AWS::Lambda::Function").values()
    }
    assert "BUCKET_UPLOADS" in functions["users-fn"]["Environment"]["Variables"]
    assert "BUCKET_UPLOADS" in functions["reports-fn"]["Environment"]["Variables"]
    assert "Environment" not in functions["worker-fn"]
    assert "Environment" not in functions["audit-fn"]


def test_iam_is_limited_to_granted_buckets(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    policies = t.find_resources("AWS::IAM::Policy")

    def actions(policy: Mapping[str, Any]) -> set[str]:
        found: set[str] = set()
        for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
            action = statement["Action"]
            found.update(action if isinstance(action, list) else [action])
        return found

    all_actions = [actions(policy) for policy in policies.values()]
    assert sum("s3:PutObject" in a for a in all_actions) == 1  # users only
    assert sum("s3:GetObject" in a for a in all_actions) == 2  # users + reports
    assert sum("s3:DeleteObject" in a for a in all_actions) == 1  # users only
    for found in all_actions:
        assert "*" not in found
        assert "s3:*" not in found

    text = json.dumps(policies)
    assert "Uploads" in text
    assert "Website" not in text  # no Lambda can touch the website or assets buckets
    assert "Assets" not in text


def test_routes_go_to_the_right_lambdas(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    for part in ("api", "users", "reports"):
        t.has_resource_properties("AWS::ApiGateway::Resource", {"PathPart": part})
    t.resource_properties_count_is("AWS::ApiGateway::Resource", {"PathPart": "{proxy+}"}, 2)

    function_ids = {
        res["Properties"]["FunctionName"]: logical_id
        for logical_id, res in t.find_resources("AWS::Lambda::Function").items()
    }
    proxy_methods = [
        res["Properties"]
        for res in t.find_resources("AWS::ApiGateway::Method").values()
        if res["Properties"].get("Integration", {}).get("Type") == "AWS_PROXY"
    ]
    assert len(proxy_methods) == 4  # 2 routes x (prefix + {proxy+})
    targets: set[str] = set()
    for props in proxy_methods:
        text = json.dumps(props["Integration"])
        targets.update(name for name, logical_id in function_ids.items() if logical_id in text)
    assert targets == {"users-fn", "reports-fn"}


def test_topic_is_shared_by_two_lambdas(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    t.resource_count_is("AWS::SNS::Topic", 1)
    t.resource_count_is("AWS::SNS::Subscription", 2)
    t.resource_count_is("AWS::SNS::TopicPolicy", 1)


def test_schedule_only_for_the_lambda_that_asked(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    t.resource_count_is("AWS::Events::Rule", 1)
    t.has_resource_properties("AWS::Events::Rule", {"ScheduleExpression": "rate(1 day)"})


def test_outputs_exist_per_resource(build: Build, lambda_dir: str) -> None:
    outputs = build(**multi(lambda_dir)).to_json()["Outputs"]
    for name in (
        "SiteUrl",
        "WebsiteBucketName",
        "AssetsBucketName",
        "UploadsBucketName",
        "UsersFunctionName",
        "ReportsFunctionName",
        "OrderWorkerFunctionName",
        "AuditFunctionName",
        "OrdersTopicArn",
    ):
        assert name in outputs


def test_standard_tags_on_every_lambda(build: Build, lambda_dir: str) -> None:
    t = build(**multi(lambda_dir))
    for resource in t.find_resources("AWS::Lambda::Function").values():
        keys = {item["Key"] for item in resource["Properties"]["Tags"]}
        assert {"Environment", "Owner", "ManagedBy"} <= keys


def test_prod_multi_stack_retains_everything(build: Build, lambda_dir: str) -> None:
    t = build(environment="prod", **multi(lambda_dir))
    for resource in t.find_resources("AWS::S3::Bucket").values():
        assert resource["DeletionPolicy"] == "Retain"
        assert resource["Properties"]["VersioningConfiguration"] == {"Status": "Enabled"}
    t.resource_properties_count_is("AWS::Logs::LogGroup", {"RetentionInDays": 90}, 5)
