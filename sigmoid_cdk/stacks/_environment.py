"""Decide which AWS account and region a stack is deployed to."""

import os

from aws_cdk import Environment

from ..configs import AwsEnvConfig


def resolve_environment(
    aws: AwsEnvConfig | None, explicit: Environment | None = None
) -> Environment | None:
    """Pick the environment: explicit env, then config, then the CDK CLI's defaults.

    The CDK CLI sets CDK_DEFAULT_ACCOUNT / CDK_DEFAULT_REGION from the current credentials
    and profile for `cdk synth` and `cdk deploy`. Each field is resolved on its own.
    Returns None (environment-agnostic) when nothing is known.
    """
    if explicit is not None:
        return explicit
    account = (aws.account if aws else None) or os.environ.get("CDK_DEFAULT_ACCOUNT") or None
    region = (aws.region if aws else None) or os.environ.get("CDK_DEFAULT_REGION") or None
    if account is None and region is None:
        return None
    return Environment(account=account, region=region)
