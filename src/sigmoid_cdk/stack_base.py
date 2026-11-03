"""SigmoidStack: base class that attaches all governance aspects to a stack."""

from typing import Any

import aws_cdk as cdk
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.aspects.compliance_aspect import attach_compliance_checks
from sigmoid_cdk.aspects.iam_guardrail_aspect import IamGuardrailAspect
from sigmoid_cdk.aspects.permissions_boundary_aspect import PermissionsBoundaryAspect
from sigmoid_cdk.aspects.tagging_aspect import TaggingAspect
from sigmoid_cdk.feature_flags import FeatureFlags
from sigmoid_cdk.helpers.environment_helper import policy_for_stage
from sigmoid_cdk.helpers.name_helper import stack_name
from sigmoid_cdk.helpers.tag_helper import build_standard_tags


class SigmoidStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        flags: FeatureFlags | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("stack_name", stack_name(context))
        kwargs.setdefault(
            "termination_protection",
            policy_for_stage(context.stage).termination_protection,
        )
        super().__init__(scope, construct_id, **kwargs)
        self.sigmoid_context = context
        self.flags = flags or FeatureFlags()
        self._attach_governance()

    def _attach_governance(self) -> None:
        aspects = cdk.Aspects.of(self)
        aspects.add(TaggingAspect(build_standard_tags(self.sigmoid_context)))
        if self.flags.iam_guardrails:
            aspects.add(IamGuardrailAspect())
        if self.flags.permissions_boundary_policy_name:
            aspects.add(
                PermissionsBoundaryAspect(self.flags.permissions_boundary_policy_name)
            )
        if self.flags.compliance_checks:
            attach_compliance_checks(self)
