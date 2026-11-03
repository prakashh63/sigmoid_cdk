from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.helpers.iam_policy_helper import (
    find_policy_violations,
    find_trust_violations,
)
from sigmoid_cdk.helpers.name_helper import (
    physical_name,
    to_pascal_case,
    to_upper_snake_case,
)
from sigmoid_cdk.helpers.tag_helper import build_standard_tags

CONTEXT = SigmoidContext("sigmoid", "orders-app", "dev", "orders-team", "cc-1")


def test_case_conversions() -> None:
    assert to_pascal_case("orders-api") == "OrdersApi"
    assert to_upper_snake_case("order-events") == "ORDER_EVENTS"


def test_physical_name() -> None:
    assert physical_name(CONTEXT, "orders-api") == "orders-app-dev-orders-api"


def test_standard_tags() -> None:
    tags = build_standard_tags(CONTEXT)
    assert tags["Environment"] == "dev"
    assert tags["Owner"] == "orders-team"
    assert tags["ManagedBy"] == "sigmoid-cdk"


def test_policy_violations() -> None:
    bad = {"Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}
    assert len(find_policy_violations(bad)) == 2
    good = {
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": "arn:aws:s3:::b/*",
            }
        ]
    }
    assert find_policy_violations(good) == []
    xray = {
        "Statement": [
            {"Effect": "Allow", "Action": "xray:PutTraceSegments", "Resource": "*"}
        ]
    }
    assert find_policy_violations(xray) == []


def test_trust_violations() -> None:
    assert find_trust_violations(
        {"Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}}]}
    )
    assert not find_trust_violations(
        {
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}
            ]
        }
    )
