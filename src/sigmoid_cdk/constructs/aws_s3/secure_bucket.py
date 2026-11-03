"""S3 bucket that is private, encrypted, HTTPS-only and versioned in production."""

from aws_cdk import aws_s3 as s3
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.s3_config import S3Config
from sigmoid_cdk.helpers.environment_helper import policy_for_stage


class SecureBucket(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: S3Config,
    ) -> None:
        super().__init__(scope, construct_id)
        stage_policy = policy_for_stage(context.stage)
        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=config.bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=stage_policy.bucket_versioning,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            removal_policy=stage_policy.removal_policy,
            auto_delete_objects=config.auto_delete_objects,
        )
