"""ServerlessWebAppStack: the one class a developer needs."""

from typing import Any


from aws_cdk import Aspects, CfnOutput, Stack
from aws_cdk import aws_sns as sns
from aws_cdk import aws_s3 as s3
from constructs import Construct

from ..aspects import TaggingAspect, enable_compliance_checks
from ..configs import WebAppConfig
from ..constructs import (
    LambdaTriggers,
    LogKey,
    SecureBucket,
    SecureTopic,
    ServerlessBackend,
    WebDistribution,
)
from ..constructs._common import env_key, pascal


class ServerlessWebAppStack(Stack):
    """Any number of Lambdas, buckets and topics, plus API Gateway, CloudFront and triggers."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: WebAppConfig,
        enable_compliance: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config
        environment = config.environment

        # 1. One optional customer-managed key shared by every log group
        self.log_key: LogKey | None = (
            LogKey(self, "LogKey", environment=environment) if config.encrypt_logs else None
        )
        key = self.log_key.key if self.log_key is not None else None

        # 2. Buckets (private; CloudFront access is added in step 6)
        self.buckets: dict[str, SecureBucket] = {
            bucket_key: SecureBucket(
                self,
                f"{pascal(bucket_key)}Bucket",
                bucket_name=bucket_config.bucket_name,
                environment=environment,
                auto_delete_objects=bucket_config.auto_delete_objects,
            )
            for bucket_key, bucket_config in config.buckets.items()
        }

        # 3. Shared SNS topics
        self.topics: dict[str, SecureTopic] = {
            topic_key: SecureTopic(
                self, f"{pascal(topic_key)}Topic", topic_name=topic_config.topic_name
            )
            for topic_key, topic_config in config.topics.items()
        }

        # 4. Lambdas (+ one API Gateway with a route table, when enabled)
        self.backend = ServerlessBackend(
            self,
            "Backend",
            lambda_configs=config.lambdas,
            api_config=config.api_gateway,
            routes=config.effective_routes(),
            environment=environment,
            log_key=key,
        )

        # 5. Wire each Lambda: bucket access (least privilege) and triggers
        topic_refs: dict[str, sns.ITopic] = {k: t.topic for k, t in self.topics.items()}
        self.triggers: dict[str, LambdaTriggers] = {}
        for lambda_key, lambda_config in config.lambdas.items():
            secure_lambda = self.backend.lambdas[lambda_key]
            for bucket_key, access in lambda_config.bucket_access.items():
                secure_lambda.grant_bucket(
                    self.buckets[bucket_key].bucket, access, env_name=env_key(bucket_key)
                )
            self.triggers[lambda_key] = LambdaTriggers(
                self,
                f"{pascal(lambda_key)}Triggers",
                function=secure_lambda.function,
                config=lambda_config.triggers,
                topics=topic_refs,
            )

        # 6. CloudFront, only when one bucket is the default origin
        default_key = next((k for k, b in config.buckets.items() if b.cdn_default), None)
        self.cdn: WebDistribution | None = None
        if default_key is not None:
            path_buckets: dict[str, s3.IBucket] = {
                bucket_config.cdn_path: self.buckets[bucket_key].bucket
                for bucket_key, bucket_config in config.buckets.items()
                if bucket_config.cdn_path is not None
            }
            self.cdn = WebDistribution(
                self,
                "Cdn",
                default_bucket=self.buckets[default_key].bucket,
                path_buckets=path_buckets,
                api=self.backend.rest_api,
            )
            CfnOutput(
                self, "SiteUrl", value=f"https://{self.cdn.distribution.distribution_domain_name}"
            )

        # 7. Outputs, one per named resource
        for bucket_key, secure_bucket in self.buckets.items():
            CfnOutput(
                self, f"{pascal(bucket_key)}BucketName", value=secure_bucket.bucket.bucket_name
            )
        for lambda_key, secure_lambda in self.backend.lambdas.items():
            CfnOutput(
                self,
                f"{pascal(lambda_key)}FunctionName",
                value=secure_lambda.function.function_name,
            )
        for topic_key, secure_topic in self.topics.items():
            CfnOutput(self, f"{pascal(topic_key)}TopicArn", value=secure_topic.topic.topic_arn)

        # 8. Governance: standard tags on every taggable resource
        tags = {
            "Environment": environment,
            "Owner": config.owner_team,
            "ManagedBy": "sigmoid_cdk",
        }
        if config.cost_center:
            tags["CostCenter"] = config.cost_center
        Aspects.of(self).add(TaggingAspect(tags))

        # 9. Governance: security gate (cdk-nag AwsSolutionsChecks)
        if enable_compliance:
            enable_compliance_checks(self)
