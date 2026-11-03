"""Shared configs for tests."""

from pathlib import Path

from sigmoid_cdk.configs import (
    ApiGatewayConfig,
    ApiRouteConfig,
    AppSettings,
    EventRuleConfig,
    LambdaConfig,
    QueueConfig,
    S3Config,
    WebAppConfig,
)

LAMBDA_SRC = str(Path(__file__).parent / "lambda_src")


def simple_settings(environment: str = "dev") -> AppSettings:
    return AppSettings(
        app_name="customer-portal",
        environment=environment,  # type: ignore[arg-type]
        owner_team="frontend-devs",
        cost_center="cc-100",
        s3=S3Config(bucket_name=f"cust-portal-web-assets-{environment}"),
        lambda_backend=LambdaConfig(
            function_name="portal-api-handler", entry_point_dir=LAMBDA_SRC
        ),
        api_gateway=ApiGatewayConfig(stage_name="v1", rate_limit=2000),
    )


def full_config(environment: str = "dev") -> WebAppConfig:
    return WebAppConfig(
        app_name="orders-app",
        environment=environment,  # type: ignore[arg-type]
        owner_team="orders-team",
        cost_center="cc-200",
        frontend_bucket=S3Config(bucket_name=f"orders-web-{environment}"),
        extra_buckets=[S3Config(bucket_name=f"orders-data-{environment}")],
        lambdas=[
            LambdaConfig(
                function_name="orders-api",
                entry_point_dir=LAMBDA_SRC,
                send_to_queues=["order-events"],
                read_write_buckets=[f"orders-data-{environment}"],
            ),
            LambdaConfig(
                function_name="order-worker",
                entry_point_dir=LAMBDA_SRC,
                timeout_seconds=60,
            ),
        ],
        api_gateways=[
            ApiGatewayConfig(
                api_name="orders-gateway",
                routes=[
                    ApiRouteConfig(
                        path="api/orders", http_method="GET", lambda_name="orders-api"
                    )
                ],
            )
        ],
        queues=[QueueConfig(queue_name="order-events", consumer_lambda="order-worker")],
        event_rules=[
            EventRuleConfig(
                rule_name="nightly-cleanup",
                schedule_expression="rate(1 day)",
                target_lambda="order-worker",
            )
        ],
    )
