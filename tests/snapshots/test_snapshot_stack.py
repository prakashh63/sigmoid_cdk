from pathlib import Path
from typing import Any

import aws_cdk as cdk
from aws_cdk.assertions import Template
from syrupy.assertion import SnapshotAssertion

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import WebAppConfig

LAMBDA_SRC = Path(__file__).parents[1] / "fixtures" / "lambda_src"


def fn(name: str, **extra: Any) -> dict[str, Any]:
    return {"function_name": name, "entry_point_dir": str(LAMBDA_SRC), **extra}


def synth(**overrides: Any) -> Any:
    data: dict[str, Any] = {
        "app_name": "snapshot-app",
        "environment": "dev",
        "owner_team": "platform",
        "cost_center": "CC-1",
        "buckets": {"web": {"bucket_name": "snapshot-assets-bucket", "cdn_default": True}},
        "lambdas": {"backend": fn("snap-fn")},
    }
    data.update(overrides)
    app = cdk.App(context={"aws:cdk:version-reporting": False})
    config = WebAppConfig.model_validate(data)
    stack = ServerlessWebAppStack(app, "SnapStack", config=config, enable_compliance=False)
    return Template.from_stack(stack).to_json()


def test_dev_stack_snapshot(snapshot: SnapshotAssertion) -> None:
    assert synth() == snapshot


def test_prod_stack_snapshot(snapshot: SnapshotAssertion) -> None:
    assert synth(environment="prod") == snapshot


def test_worker_stack_snapshot(snapshot: SnapshotAssertion) -> None:
    worker = synth(
        buckets={},
        api_gateway={"enable_proxy": False},
        topics={"orders": {"topic_name": "snapshot-topic"}},
        lambdas={
            "worker": fn(
                "snap-fn",
                triggers={
                    "schedule": {"expression": "rate(1 hour)"},
                    "event_rule": {
                        "source": ["orders.service"],
                        "detail_type": ["Order Created"],
                    },
                    "sns": ["orders"],
                },
            )
        },
    )
    assert worker == snapshot


def test_multi_stack_snapshot(snapshot: SnapshotAssertion) -> None:
    multi = synth(
        buckets={
            "website": {"bucket_name": "snapshot-web-bucket", "cdn_default": True},
            "assets": {"bucket_name": "snapshot-assets-bucket", "cdn_path": "/assets/*"},
            "uploads": {"bucket_name": "snapshot-uploads-bucket"},
        },
        topics={"orders": {"topic_name": "snapshot-topic"}},
        lambdas={
            "users": fn("snap-users", bucket_access={"uploads": "read_write"}),
            "reports": fn(
                "snap-reports",
                bucket_access={"uploads": "read"},
                triggers={"schedule": {"expression": "rate(1 day)"}},
            ),
            "order-worker": fn("snap-worker", triggers={"sns": ["orders"]}),
        },
        api_gateway={
            "routes": [
                {"path": "/api/users", "function": "users"},
                {"path": "/api/reports", "function": "reports"},
            ]
        },
    )
    assert multi == snapshot
