from collections.abc import Callable
from typing import Any

from aws_cdk.assertions import Match, Template

Build = Callable[..., Template]


def worker(
    lambda_dir: str, triggers: dict[str, Any], topics: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Config overrides for a worker-only stack: no bucket, no API."""
    data: dict[str, Any] = {
        "buckets": {},
        "api_gateway": {"enable_proxy": False},
        "lambdas": {
            "backend": {
                "function_name": "demo-fn",
                "entry_point_dir": lambda_dir,
                "triggers": triggers,
            }
        },
    }
    if topics:
        data["topics"] = topics
    return data


def test_no_triggers_by_default(build: Build) -> None:
    t = build()
    t.resource_count_is("AWS::Events::Rule", 0)
    t.resource_count_is("AWS::SNS::Topic", 0)


def test_schedule_trigger(build: Build, lambda_dir: str) -> None:
    t = build(**worker(lambda_dir, {"schedule": {"expression": "rate(1 hour)"}}))
    t.has_resource_properties(
        "AWS::Events::Rule",
        {
            "ScheduleExpression": "rate(1 hour)",
            "Targets": Match.array_with([Match.object_like({"Arn": Match.any_value()})]),
        },
    )
    t.has_resource_properties("AWS::Lambda::Permission", {"Principal": "events.amazonaws.com"})


def test_event_pattern_trigger(build: Build, lambda_dir: str) -> None:
    t = build(
        **worker(
            lambda_dir,
            {"event_rule": {"source": ["orders.service"], "detail_type": ["Order Created"]}},
        )
    )
    t.has_resource_properties(
        "AWS::Events::Rule",
        {"EventPattern": {"source": ["orders.service"], "detail-type": ["Order Created"]}},
    )


def test_sns_trigger_is_encrypted_and_ssl_only(build: Build, lambda_dir: str) -> None:
    t = build(
        **worker(
            lambda_dir,
            {"sns": ["orders"]},
            topics={"orders": {"topic_name": "orders-topic"}},
        )
    )
    t.resource_count_is("AWS::SNS::Topic", 1)
    t.has_resource_properties(
        "AWS::SNS::Topic",
        {"TopicName": "orders-topic", "KmsMasterKeyId": Match.any_value()},
    )
    t.has_resource_properties("AWS::SNS::Subscription", {"Protocol": "lambda"})
    t.has_resource_properties("AWS::Lambda::Permission", {"Principal": "sns.amazonaws.com"})
    t.resource_count_is("AWS::SNS::TopicPolicy", 1)


def test_topic_without_subscribers_is_still_created(build: Build, lambda_dir: str) -> None:
    t = build(**worker(lambda_dir, {}, topics={"orders": {"topic_name": "orders-topic"}}))
    t.resource_count_is("AWS::SNS::Topic", 1)
    t.resource_count_is("AWS::SNS::Subscription", 0)


def test_all_triggers_together(build: Build, lambda_dir: str) -> None:
    t = build(
        **worker(
            lambda_dir,
            {
                "schedule": {"expression": "rate(5 minutes)"},
                "event_rule": {"source": ["a.b"]},
                "sns": ["t1"],
            },
            topics={"t1": {"topic_name": "t1-topic"}},
        )
    )
    t.resource_count_is("AWS::Events::Rule", 2)
    t.resource_count_is("AWS::SNS::Topic", 1)
    t.resource_count_is("AWS::Lambda::Function", 1)
