"""cdk-nag AwsSolutions checks. An unacknowledged error stops `cdk synth`.

Every acknowledgement below is also written in docs/cdk-nag-acknowledgments.md.
"""

from dataclasses import dataclass

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagPackSuppression, NagSuppressions


@dataclass(frozen=True)
class Acknowledgement:
    rule_id: str
    reason: str
    applies_to: tuple[str, ...] = ()


ACKNOWLEDGED_FINDINGS: tuple[Acknowledgement, ...] = (
    Acknowledgement(
        "AwsSolutions-IAM4",
        "API Gateway needs the AWS-managed push-to-CloudWatch policy for its account logging role.",
        (
            "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs",
        ),
    ),
    Acknowledgement(
        "AwsSolutions-IAM5",
        "Wildcards only appear inside specific resource ARNs (bucket/*, log-group:*). "
        "The IAM guardrail aspect rejects bare '*' actions and resources.",
    ),
    Acknowledgement(
        "AwsSolutions-S1",
        "A central S3 access-log bucket is not part of this stack yet.",
    ),
    Acknowledgement(
        "AwsSolutions-CFR1", "Geo restriction is not required for this application."
    ),
    Acknowledgement(
        "AwsSolutions-CFR2", "AWS WAF is planned as a later addition, not part of v0.1."
    ),
    Acknowledgement(
        "AwsSolutions-CFR3",
        "CloudFront access logging needs a log bucket; planned later.",
    ),
    Acknowledgement(
        "AwsSolutions-CFR4",
        "Default CloudFront certificate is used until a custom domain exists.",
    ),
    Acknowledgement(
        "AwsSolutions-APIG3",
        "AWS WAF is planned as a later addition, not part of v0.1.",
    ),
    Acknowledgement(
        "AwsSolutions-APIG4",
        "Authorization is handled inside the application until an authorizer is added.",
    ),
    Acknowledgement(
        "AwsSolutions-COG4", "No Cognito user pool is used; authorizer planned later."
    ),
)


def attach_compliance_checks(stack: cdk.Stack) -> None:
    cdk.Aspects.of(stack).add(AwsSolutionsChecks(verbose=True))
    NagSuppressions.add_stack_suppressions(
        stack,
        [
            NagPackSuppression(
                id=item.rule_id,
                reason=item.reason,
                applies_to=list(item.applies_to) if item.applies_to else None,
            )
            for item in ACKNOWLEDGED_FINDINGS
        ],
    )
