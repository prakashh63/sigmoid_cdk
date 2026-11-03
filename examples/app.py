from sigmoid_cdk import SigmoidApp
from sigmoid_cdk.configs import (
    ApiGatewayConfig,
    ApiRouteConfig,
    LambdaConfig,
    S3Config,
    WebAppConfig,
)

stage = "dev"  # change to "staging" or "prod" here

app = SigmoidApp(
    WebAppConfig(
        app_name="customer-portal",
        environment=stage,
        owner_team="frontend-devs",
        cost_center="cc-100",
        # 2 S3 buckets: website files (served by CloudFront) and app data
        frontend_bucket=S3Config(bucket_name=f"cust-portal-web-{stage}-demo"),
        extra_buckets=[S3Config(bucket_name=f"cust-portal-data-{stage}-demo")],
        # 2 Lambda functions
        lambdas=[
            LambdaConfig(
                function_name="orders-handler",
                entry_point_dir="examples/lambda_src/orders",
                memory_mb=128,
                timeout_seconds=10,
                read_write_buckets=[f"cust-portal-data-{stage}-demo"],
            ),
            LambdaConfig(
                function_name="users-handler",
                entry_point_dir="examples/lambda_src/users",
                memory_mb=128,
                timeout_seconds=10,
            ),
        ],
        # 2 API Gateways (the first one is served by CloudFront at /api/*)
        api_gateways=[
            ApiGatewayConfig(
                api_name="orders-gateway",
                stage_name="v1",
                rate_limit=5,
                burst_limit=10,
                routes=[
                    ApiRouteConfig(
                        path="api/orders",
                        http_method="GET",
                        lambda_name="orders-handler",
                    ),
                    ApiRouteConfig(
                        path="api/orders",
                        http_method="POST",
                        lambda_name="orders-handler",
                    ),
                ],
            ),
            ApiGatewayConfig(
                api_name="users-gateway",
                stage_name="v1",
                rate_limit=5,
                burst_limit=10,
                routes=[
                    ApiRouteConfig(
                        path="users/{id}",
                        http_method="GET",
                        lambda_name="users-handler",
                    ),
                ],
            ),
        ],
    )
)
app.synth()
