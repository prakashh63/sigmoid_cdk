"""SQS queue + dead-letter queue, both encrypted and HTTPS-only."""

import aws_cdk as cdk
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.messaging_config import QueueConfig
from sigmoid_cdk.helpers.name_helper import physical_name


class QueueWithDeadLetterQueue(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: QueueConfig,
        visibility_timeout: cdk.Duration,
    ) -> None:
        super().__init__(scope, construct_id)
        queue_name = physical_name(context, config.queue_name)
        self.dead_letter_queue = sqs.Queue(
            self,
            "DeadLetterQueue",
            queue_name=f"{queue_name}-dlq",
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
            retention_period=cdk.Duration.days(14),
        )
        self.queue = sqs.Queue(
            self,
            "Queue",
            queue_name=queue_name,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
            visibility_timeout=visibility_timeout,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=config.max_receive_count, queue=self.dead_letter_queue
            ),
        )
