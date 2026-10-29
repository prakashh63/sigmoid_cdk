"""SecureLambda: a Lambda function with encrypted logs and a least-privilege role.

This construct knows nothing about API Gateway, so it fits every use case:
web backends, SQS/SNS/EventBridge workers, scheduled jobs.
"""

from typing import cast

from aws_cdk import Acknowledgment, CfnElement, Duration, Stack, Validations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct

from ..configs import LambdaConfig
from ._common import log_retention, removal_policy

RUNTIMES: dict[str, _lambda.Runtime] = {
    "PYTHON_3_10": _lambda.Runtime.PYTHON_3_10,
    "PYTHON_3_11": _lambda.Runtime.PYTHON_3_11,
    "PYTHON_3_12": _lambda.Runtime.PYTHON_3_12,
    "PYTHON_3_13": _lambda.Runtime.PYTHON_3_13,
    "PYTHON_3_14": _lambda.Runtime.PYTHON_3_14,
}

# Explicit S3 actions per access level (no s3:* and no wildcard actions).
_OBJECT_ACTIONS: dict[str, list[str]] = {
    "read": ["s3:GetObject"],
    "write": ["s3:PutObject", "s3:AbortMultipartUpload"],
    "read_write": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:AbortMultipartUpload",
        "s3:DeleteObject",
    ],
}
_LISTING_LEVELS = ("read", "read_write")


class SecureLambda(Construct):
    """Function + log group (environment-aware retention) + role that can only write its logs."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        lambda_config: LambdaConfig,
        environment: str,
        log_key: kms.IKey | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.log_group = logs.LogGroup(
            self,
            "Logs",
            retention=log_retention(environment),
            removal_policy=removal_policy(environment),
            encryption_key=log_key,
        )

        # Least privilege: no AWS managed policy, only write access to this log group.
        self.role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        self.log_group.grant_write(self.role)

        self.function = _lambda.Function(
            self,
            "Function",
            function_name=lambda_config.function_name,
            runtime=RUNTIMES[lambda_config.runtime],
            handler=lambda_config.handler,
            code=_lambda.Code.from_asset(lambda_config.entry_point_dir),
            memory_size=lambda_config.memory_mb,
            timeout=Duration.seconds(lambda_config.timeout_seconds),
            environment=lambda_config.environment_vars,
            role=self.role,
            log_group=self.log_group,
        )

    def grant_bucket(self, bucket: s3.IBucket, access: str, *, env_name: str) -> None:
        """Allow this function to use ONE bucket and pass the bucket name in an env var."""
        self.role.add_to_policy(
            iam.PolicyStatement(
                actions=_OBJECT_ACTIONS[access],
                resources=[bucket.arn_for_objects("*")],
            )
        )
        if access in _LISTING_LEVELS:
            self.role.add_to_policy(
                iam.PolicyStatement(actions=["s3:ListBucket"], resources=[bucket.bucket_arn])
            )
        self.function.add_environment(env_name, bucket.bucket_name)

        # cdk-nag IAM5 reports the exact resource '<bucket>/*'. Acknowledge only that one,
        # built from the bucket's logical ID, so each Lambda is cleared for its granted buckets.
        bucket_id = Stack.of(self).get_logical_id(cast(CfnElement, bucket.node.default_child))
        Validations.of(self.role).acknowledge(
            Acknowledgment(
                id=f"AwsSolutions::AwsSolutions-IAM5[Resource::<{bucket_id}.Arn>/*]",
                reason=(
                    "Object-level access needs '<bucket>/*'. Limited to this one bucket, "
                    "which is named in the Lambda's bucket_access, with explicit S3 actions."
                ),
            )
        )
