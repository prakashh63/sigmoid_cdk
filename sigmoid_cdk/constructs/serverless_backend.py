"""ServerlessBackend: several SecureLambda functions plus an optional API Gateway in front."""

from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_kms as kms
from constructs import Construct

from ..configs import ApiGatewayConfig, LambdaConfig, RouteConfig
from .api_proxy import ApiGatewayProxy
from ._common import pascal
from .secure_lambda import SecureLambda


class ServerlessBackend(Construct):
    """One SecureLambda per config entry, and one API when there are routes."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        lambda_configs: dict[str, LambdaConfig],
        api_config: ApiGatewayConfig,
        routes: list[RouteConfig],
        environment: str,
        log_key: kms.IKey | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        # key -> SecureLambda (each has its own role and log group)
        self.lambdas: dict[str, SecureLambda] = {
            key: SecureLambda(
                self,
                pascal(key),
                lambda_config=lambda_config,
                environment=environment,
                log_key=log_key,
            )
            for key, lambda_config in lambda_configs.items()
        }

        self.rest_api: apigw.RestApi | None = None
        if api_config.enable_proxy and routes:
            proxy = ApiGatewayProxy(
                self,
                "Api",
                routes=[(route.path, self.lambdas[route.function].function) for route in routes],
                api_config=api_config,
                environment=environment,
                log_key=log_key,
            )
            self.rest_api = proxy.rest_api
