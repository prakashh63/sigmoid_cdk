"""Lambda function with its own encrypted log group and its own least-privilege role."""

from collections.abc import Sequence

import aws_cdk as cdk
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.lambda_config import LambdaConfig
from sigmoid_cdk.constructs.aws_iam.lambda_execution_role import LambdaExecutionRole
from sigmoid_cdk.constructs.aws_logs.secure_log_group import SecureLogGroup
from sigmoid_cdk.helpers.name_helper import physical_name


class SigmoidLambdaFunction(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: LambdaConfig,
        log_key: kms.IKey,
        layers: Sequence[lambda_.ILayerVersion],
    ) -> None:
        super().__init__(scope, construct_id)
        function_name = physical_name(context, config.function_name)
        log_group = SecureLogGroup(
            self,
            "LogGroup",
            context=context,
            log_group_name=f"/aws/lambda/{function_name}",
            encryption_key=log_key,
        )
        execution_role = LambdaExecutionRole(
            self,
            "ExecutionRole",
            context=context,
            function_name=config.function_name,
            log_group=log_group.log_group,
        )
        self.role = execution_role.role
        self.function = lambda_.Function(
            self,
            "Function",
            function_name=function_name,
            runtime=getattr(lambda_.Runtime, config.runtime),
            handler=config.handler,
            code=lambda_.Code.from_asset(config.entry_point_dir),
            memory_size=config.memory_mb,
            timeout=cdk.Duration.seconds(config.timeout_seconds),
            environment={"STAGE": context.stage, **config.environment_vars},
            role=self.role,
            log_group=log_group.log_group,
            layers=list(layers),
        )
