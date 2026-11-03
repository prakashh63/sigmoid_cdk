"""A Lambda layer built from a local folder."""

from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from sigmoid_cdk.application_constants import SUPPORTED_LAMBDA_RUNTIMES
from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.lambda_config import LambdaLayerConfig
from sigmoid_cdk.helpers.name_helper import physical_name


class SigmoidLambdaLayer(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: LambdaLayerConfig,
    ) -> None:
        super().__init__(scope, construct_id)
        self.layer = lambda_.LayerVersion(
            self,
            "Layer",
            layer_version_name=physical_name(context, config.layer_name),
            code=lambda_.Code.from_asset(config.source_dir),
            compatible_runtimes=[
                getattr(lambda_.Runtime, name)
                for name in SUPPORTED_LAMBDA_RUNTIMES
                if hasattr(lambda_.Runtime, name)
            ],
        )
