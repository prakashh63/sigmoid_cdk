"""One KMS key that encrypts every CloudWatch log group of the application."""

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.helpers.environment_helper import policy_for_stage


class LogEncryptionKey(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, *, context: SigmoidContext
    ) -> None:
        super().__init__(scope, construct_id)
        stack = cdk.Stack.of(self)
        self.key = kms.Key(
            self,
            "Key",
            description=f"Encrypts CloudWatch logs of {context.application} ({context.stage})",
            enable_key_rotation=True,
            removal_policy=policy_for_stage(context.stage).removal_policy,
        )
        self.key.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudWatchLogsToUseTheKey",
                principals=[iam.ServicePrincipal(f"logs.{stack.region}.amazonaws.com")],
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:Describe*",
                ],
                resources=["*"],
                conditions={
                    "ArnLike": {
                        "kms:EncryptionContext:aws:logs:arn": (
                            f"arn:{stack.partition}:logs:{stack.region}:{stack.account}:log-group:*"
                        )
                    }
                },
            )
        )
