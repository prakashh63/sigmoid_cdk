"""A log group that is always KMS-encrypted and has stage-aware retention."""

from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.helpers.environment_helper import policy_for_stage


class SecureLogGroup(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        log_group_name: str,
        encryption_key: kms.IKey,
    ) -> None:
        super().__init__(scope, construct_id)
        stage_policy = policy_for_stage(context.stage)
        self.log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name=log_group_name,
            retention=stage_policy.log_retention,  # 7 days dev, 30 staging, 90 prod
            encryption_key=encryption_key,
            removal_policy=stage_policy.removal_policy,
        )
