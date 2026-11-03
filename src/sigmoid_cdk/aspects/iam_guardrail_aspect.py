"""Aspect that fails synthesis when IAM policies are too broad (docs/iam/guardrail-rules.md)."""

import aws_cdk as cdk
import jsii
from aws_cdk import aws_iam as iam
from constructs import IConstruct

from sigmoid_cdk.helpers.iam_policy_helper import (
    find_policy_violations,
    find_trust_violations,
)

_PREFIX = "[sigmoid-cdk IAM guardrail]"


@jsii.implements(cdk.IAspect)
class IamGuardrailAspect:
    def visit(self, node: IConstruct) -> None:
        stack = cdk.Stack.of(node)
        if isinstance(node, (iam.CfnPolicy, iam.CfnManagedPolicy)):
            for message in find_policy_violations(stack.resolve(node.policy_document)):
                cdk.Annotations.of(node).add_error(f"{_PREFIX} {message}")
        if isinstance(node, iam.CfnRole):
            trust = stack.resolve(node.assume_role_policy_document)
            for message in find_trust_violations(trust):
                cdk.Annotations.of(node).add_error(f"{_PREFIX} {message}")
