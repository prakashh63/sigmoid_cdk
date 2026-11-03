"""All Lambda layers, Lambda functions and API Gateways of one application."""

from collections.abc import Sequence

from aws_cdk import aws_kms as kms
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.api_gateway_config import ApiGatewayConfig
from sigmoid_cdk.configs.lambda_config import LambdaConfig, LambdaLayerConfig
from sigmoid_cdk.constructs.aws_apigateway.api_gateway_rest_api import SigmoidRestApi
from sigmoid_cdk.constructs.aws_lambda.lambda_function import SigmoidLambdaFunction
from sigmoid_cdk.constructs.aws_lambda.lambda_layer import SigmoidLambdaLayer
from sigmoid_cdk.helpers.lambda_layers_helper import select_layers
from sigmoid_cdk.helpers.name_helper import to_pascal_case


class ServerlessBackend(Construct):
    """Exposes `functions` and `apis` as dictionaries keyed by the names in the config."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        layer_configs: Sequence[LambdaLayerConfig],
        lambda_configs: Sequence[LambdaConfig],
        api_configs: Sequence[ApiGatewayConfig],
        log_key: kms.IKey,
    ) -> None:
        super().__init__(scope, construct_id)

        layers = {
            cfg.layer_name: SigmoidLambdaLayer(
                self,
                f"{to_pascal_case(cfg.layer_name)}Layer",
                context=context,
                config=cfg,
            ).layer
            for cfg in layer_configs
        }
        self.functions: dict[str, SigmoidLambdaFunction] = {
            cfg.function_name: SigmoidLambdaFunction(
                self,
                f"{to_pascal_case(cfg.function_name)}Function",
                context=context,
                config=cfg,
                log_key=log_key,
                layers=select_layers(layers, cfg.layer_names),
            )
            for cfg in lambda_configs
        }
        function_handles = {name: fn.function for name, fn in self.functions.items()}
        self.apis: dict[str, SigmoidRestApi] = {
            cfg.api_name: SigmoidRestApi(
                self,
                f"{to_pascal_case(cfg.api_name)}Api",
                context=context,
                config=cfg,
                log_key=log_key,
                functions=function_handles,
            )
            for cfg in api_configs
        }
