"""LambdaTriggers: optional EventBridge and SNS event sources for ONE Lambda function."""

from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subs
from constructs import Construct

from ..configs import TriggerConfig


class LambdaTriggers(Construct):
    """Creates only the triggers present in the config; an empty config creates nothing.

    SNS topics are shared: they are created once elsewhere and passed in by key.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        function: _lambda.IFunction,
        config: TriggerConfig,
        topics: dict[str, sns.ITopic],
    ) -> None:
        super().__init__(scope, construct_id)

        self.schedule_rule: events.Rule | None = None
        self.event_rule: events.Rule | None = None

        if config.schedule is not None:
            self.schedule_rule = events.Rule(
                self,
                "ScheduleRule",
                description="Scheduled trigger created by sigmoid_cdk",
                schedule=events.Schedule.expression(config.schedule.expression),
            )
            self.schedule_rule.add_target(targets.LambdaFunction(function, retry_attempts=2))

        if config.event_rule is not None:
            rule_config = config.event_rule
            bus = (
                events.EventBus.from_event_bus_name(self, "Bus", rule_config.event_bus_name)
                if rule_config.event_bus_name
                else None
            )
            self.event_rule = events.Rule(
                self,
                "EventRule",
                description="Event pattern trigger created by sigmoid_cdk",
                event_bus=bus,
                event_pattern=events.EventPattern(
                    source=rule_config.source,
                    detail_type=rule_config.detail_type or None,
                ),
            )
            self.event_rule.add_target(targets.LambdaFunction(function, retry_attempts=2))

        for topic_key in config.sns:
            topics[topic_key].add_subscription(subs.LambdaSubscription(function))
