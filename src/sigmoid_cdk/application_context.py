"""SigmoidContext: the who/what/where facts every construct needs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sigmoid_cdk.application_types import Stage

if TYPE_CHECKING:
    from sigmoid_cdk.configs.web_app_config import WebAppConfig


@dataclass(frozen=True)
class SigmoidContext:
    """Organization, application, stage, owner and cost centre of one deployment."""

    organization: str
    application: str
    stage: Stage
    owner: str
    cost_center: str

    @property
    def is_production(self) -> bool:
        return self.stage == "prod"

    @classmethod
    def from_config(cls, config: WebAppConfig) -> SigmoidContext:
        return cls(
            organization=config.organization,
            application=config.app_name,
            stage=config.environment,
            owner=config.owner_team,
            cost_center=config.cost_center,
        )
