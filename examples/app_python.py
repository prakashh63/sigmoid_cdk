# Same stack, configured in Python instead of YAML.
# (The original assignment form  WebAppConfig(s3=..., lambda_backend=...)  still works too.)
import aws_cdk as cdk

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import ApiGatewayConfig, LambdaConfig, S3Config, WebAppConfig

app = cdk.App()

config = WebAppConfig(
    app_name="customer-portal",
    environment="prod",
    owner_team="frontend-devs",
    buckets={"web": S3Config(bucket_name="cust-portal-web-assets-prod", cdn_default=True)},
    lambdas={
        "backend": LambdaConfig(
            function_name="portal-api-handler",
            entry_point_dir="src/backend_lambda",  # relative to the folder you run cdk from
            memory_mb=1024,
            environment_vars={"TABLE_NAME": "Customers"},
        )
    },
    api_gateway=ApiGatewayConfig(stage_name="v1", rate_limit=2000),
)

ServerlessWebAppStack(app, "CustomerPortalProdStack", config=config)
app.synth()
