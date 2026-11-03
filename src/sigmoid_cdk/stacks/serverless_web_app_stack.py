"""ServerlessWebAppStack: S3 + CloudFront + API Gateway + Lambda (+ SQS, EventBridge)."""

from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_lambda_event_sources as event_sources
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.web_app_config import WebAppConfig
from sigmoid_cdk.constructs.aws_cloudfront.web_distribution import WebDistribution
from sigmoid_cdk.constructs.aws_events.event_rule import SigmoidEventRule
from sigmoid_cdk.constructs.aws_kms.log_encryption_key import LogEncryptionKey
from sigmoid_cdk.constructs.aws_s3.secure_bucket import SecureBucket
from sigmoid_cdk.constructs.aws_sqs.queue_with_dead_letter_queue import (
    QueueWithDeadLetterQueue,
)
from sigmoid_cdk.constructs.serverless_backend.serverless_backend import (
    ServerlessBackend,
)
from sigmoid_cdk.feature_flags import FeatureFlags
from sigmoid_cdk.helpers.name_helper import to_pascal_case, to_upper_snake_case
from sigmoid_cdk.stack_base import SigmoidStack

_VISIBILITY_TIMEOUT_FACTOR = 6  # AWS guidance: at least 6x the consumer's timeout


class ServerlessWebAppStack(SigmoidStack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: WebAppConfig,
        context: SigmoidContext | None = None,
        flags: FeatureFlags | None = None,
        **kwargs: Any,
    ) -> None:
        sigmoid_context = context or SigmoidContext.from_config(config)
        super().__init__(
            scope, construct_id, context=sigmoid_context, flags=flags, **kwargs
        )

        log_key = LogEncryptionKey(self, "LogEncryptionKey", context=sigmoid_context)

        buckets = {
            cfg.bucket_name: SecureBucket(
                self,
                f"{to_pascal_case(cfg.bucket_name)}Bucket",
                context=sigmoid_context,
                config=cfg,
            )
            for cfg in [config.frontend_bucket, *config.extra_buckets]
        }

        timeouts = {f.function_name: f.timeout_seconds for f in config.lambdas}
        queues = {
            q.queue_name: QueueWithDeadLetterQueue(
                self,
                f"{to_pascal_case(q.queue_name)}Queue",
                context=sigmoid_context,
                config=q,
                visibility_timeout=cdk.Duration.seconds(
                    _VISIBILITY_TIMEOUT_FACTOR
                    * timeouts.get(q.consumer_lambda or "", 30)
                ),
            )
            for q in config.queues
        }

        backend = ServerlessBackend(
            self,
            "Backend",
            context=sigmoid_context,
            layer_configs=config.layers,
            lambda_configs=config.lambdas,
            api_configs=config.api_gateways,
            log_key=log_key.key,
        )

        for fn_config in config.lambdas:
            fn = backend.functions[fn_config.function_name]
            for queue_name in fn_config.send_to_queues:
                queues[queue_name].queue.grant_send_messages(fn.role)
                fn.function.add_environment(
                    f"QUEUE_URL_{to_upper_snake_case(queue_name)}",
                    queues[queue_name].queue.queue_url,
                )
            for bucket_name in fn_config.read_write_buckets:
                buckets[bucket_name].bucket.grant_read_write(fn.role)
                fn.function.add_environment(
                    f"BUCKET_NAME_{to_upper_snake_case(bucket_name)}",
                    buckets[bucket_name].bucket.bucket_name,
                )

        for q in config.queues:
            if q.consumer_lambda is not None:
                backend.functions[q.consumer_lambda].function.add_event_source(
                    event_sources.SqsEventSource(
                        queues[q.queue_name].queue, batch_size=q.batch_size
                    )
                )

        for rule in config.event_rules:
            SigmoidEventRule(
                self,
                f"{to_pascal_case(rule.rule_name)}Rule",
                context=sigmoid_context,
                config=rule,
                target_function=backend.functions[rule.target_lambda].function
                if rule.target_lambda
                else None,
                target_queue=queues[rule.target_queue].queue
                if rule.target_queue
                else None,
            )

        served_api = config.cloudfront_api
        distribution = WebDistribution(
            self,
            "WebDistribution",
            context=sigmoid_context,
            config=config.cloudfront,
            frontend_bucket=buckets[config.frontend_bucket.bucket_name].bucket,
            api=backend.apis[served_api.api_name].rest_api if served_api else None,
        )

        cdk.CfnOutput(
            self,
            "SiteUrl",
            value=f"https://{distribution.distribution.distribution_domain_name}",
        )
        cdk.CfnOutput(
            self, "FrontendBucketName", value=config.frontend_bucket.bucket_name
        )
        for api_name, api in backend.apis.items():
            cdk.CfnOutput(
                self, f"{to_pascal_case(api_name)}ApiUrl", value=api.rest_api.url
            )
