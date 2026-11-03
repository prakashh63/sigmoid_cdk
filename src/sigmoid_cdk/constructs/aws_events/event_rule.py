"""EventBridge rule with a schedule or an event pattern, and one target."""

from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.messaging_config import EventRuleConfig
from sigmoid_cdk.helpers.name_helper import physical_name


class SigmoidEventRule(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: EventRuleConfig,
        target_function: lambda_.IFunction | None = None,
        target_queue: sqs.IQueue | None = None,
    ) -> None:
        super().__init__(scope, construct_id)
        schedule = (
            events.Schedule.expression(config.schedule_expression)
            if config.schedule_expression
            else None
        )
        pattern = (
            events.EventPattern(
                source=config.event_source, detail_type=config.detail_types or None
            )
            if config.event_source
            else None
        )
        self.rule = events.Rule(
            self,
            "Rule",
            rule_name=physical_name(context, config.rule_name),
            description=config.description or None,
            schedule=schedule,
            event_pattern=pattern,
        )
        if target_function is not None:
            self.rule.add_target(targets.LambdaFunction(target_function))
        if target_queue is not None:
            self.rule.add_target(targets.SqsQueue(target_queue))
