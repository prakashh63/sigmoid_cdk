"""One table that says how each stage (dev, staging, prod) behaves."""

from collections.abc import Mapping
from dataclasses import dataclass

import aws_cdk as cdk
from aws_cdk import aws_logs as logs

from sigmoid_cdk.application_types import Stage


@dataclass(frozen=True)
class StagePolicy:
    """Behaviour that changes with the stage."""

    log_retention: logs.RetentionDays
    bucket_versioning: bool
    removal_policy: cdk.RemovalPolicy
    termination_protection: bool


STAGE_POLICIES: Mapping[Stage, StagePolicy] = {
    "dev": StagePolicy(
        logs.RetentionDays.ONE_WEEK, False, cdk.RemovalPolicy.DESTROY, False
    ),
    "staging": StagePolicy(
        logs.RetentionDays.ONE_MONTH, False, cdk.RemovalPolicy.DESTROY, False
    ),
    "prod": StagePolicy(
        logs.RetentionDays.THREE_MONTHS, True, cdk.RemovalPolicy.RETAIN, True
    ),
}
