"""Naming rules in one place (see docs/naming-conventions.md)."""

import re

from sigmoid_cdk.application_context import SigmoidContext


def to_pascal_case(text: str) -> str:
    """'orders-api' -> 'OrdersApi'. Used for construct ids."""
    return "".join(
        word.capitalize() for word in re.split(r"[^A-Za-z0-9]+", text) if word
    )


def to_upper_snake_case(text: str) -> str:
    """'orders-queue' -> 'ORDERS_QUEUE'. Used for environment variable names."""
    return "_".join(word.upper() for word in re.split(r"[^A-Za-z0-9]+", text) if word)


def physical_name(context: SigmoidContext, *parts: str) -> str:
    """Name of an AWS resource: '<application>-<stage>-<part>-...'."""
    return "-".join([context.application, context.stage, *parts])


def stack_name(context: SigmoidContext) -> str:
    """Name of the CloudFormation stack: '<organization>-<application>-<stage>'."""
    return f"{context.organization}-{context.application}-{context.stage}"
