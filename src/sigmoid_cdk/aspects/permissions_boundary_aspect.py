"""Aspect that attaches a permissions boundary to every IAM role (optional feature)."""

import aws_cdk as cdk
import jsii
from aws_cdk import aws_iam as iam
from constructs import IConstruct


@jsii.implements(cdk.IAspect)
class PermissionsBoundaryAspect:
    def __init__(self, boundary_policy_name: str) -> None:
        self._arn = f"arn:{cdk.Aws.PARTITION}:iam::{cdk.Aws.ACCOUNT_ID}:policy/{boundary_policy_name}"

    def visit(self, node: IConstruct) -> None:
        if isinstance(node, iam.CfnRole) and node.permissions_boundary is None:
            node.permissions_boundary = self._arn
