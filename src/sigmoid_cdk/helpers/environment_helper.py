"""Looks up stage-specific behaviour."""

from sigmoid_cdk.application_types import Stage
from sigmoid_cdk.utilities.stage_policies import STAGE_POLICIES, StagePolicy


def policy_for_stage(stage: Stage) -> StagePolicy:
    return STAGE_POLICIES[stage]
