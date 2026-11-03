"""Settings for SQS queues and EventBridge rules."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sigmoid_cdk.utilities.validators import (
    require_kebab_case,
    require_schedule_expression,
)


class QueueConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queue_name: str
    max_receive_count: int = Field(default=3, ge=1, le=1000)
    consumer_lambda: str | None = None  # function_name that reads the queue
    batch_size: int = Field(default=10, ge=1, le=10)

    @field_validator("queue_name")
    @classmethod
    def _check_queue_name(cls, value: str) -> str:
        return require_kebab_case(value)


class EventRuleConfig(BaseModel):
    """A rule fires on a schedule OR on events from named sources, and has one target."""

    model_config = ConfigDict(extra="forbid")

    rule_name: str
    description: str = ""
    schedule_expression: str | None = None
    event_source: list[str] | None = None
    detail_types: list[str] = Field(default_factory=list)
    target_lambda: str | None = None
    target_queue: str | None = None

    @field_validator("rule_name")
    @classmethod
    def _check_rule_name(cls, value: str) -> str:
        return require_kebab_case(value)

    @field_validator("schedule_expression")
    @classmethod
    def _check_schedule(cls, value: str | None) -> str | None:
        return None if value is None else require_schedule_expression(value)

    @model_validator(mode="after")
    def _check_trigger_and_target(self) -> Self:
        if (self.schedule_expression is None) == (self.event_source is None):
            raise ValueError("set exactly one of schedule_expression or event_source")
        if (self.target_lambda is None) == (self.target_queue is None):
            raise ValueError("set exactly one of target_lambda or target_queue")
        return self
