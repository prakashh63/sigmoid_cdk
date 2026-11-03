"""Builds the standard company tags."""

from sigmoid_cdk.application_constants import (
    MANAGED_BY_TAG_VALUE,
    TAG_APPLICATION,
    TAG_COST_CENTER,
    TAG_ENVIRONMENT,
    TAG_MANAGED_BY,
    TAG_OWNER,
)
from sigmoid_cdk.application_context import SigmoidContext


def build_standard_tags(context: SigmoidContext) -> dict[str, str]:
    """Tags that must be on every taggable resource."""
    return {
        TAG_ENVIRONMENT: context.stage,
        TAG_OWNER: context.owner,
        TAG_COST_CENTER: context.cost_center,
        TAG_MANAGED_BY: MANAGED_BY_TAG_VALUE,
        TAG_APPLICATION: context.application,
    }
