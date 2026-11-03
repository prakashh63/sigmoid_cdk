"""Small validation functions reused by the pydantic config models."""

import re
from collections.abc import Iterable

_KEBAB_CASE = re.compile(r"^[a-z][a-z0-9-]{1,38}[a-z0-9]$")
_BUCKET_NAME = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_SCHEDULE_EXPRESSION = re.compile(r"^(rate|cron)\(.+\)$")


def require_kebab_case(value: str) -> str:
    """Names used in resource ids must be lower-case words joined by hyphens."""
    if not _KEBAB_CASE.match(value):
        raise ValueError(
            f"'{value}' must be kebab-case, 3 to 40 characters (example: orders-api)"
        )
    return value


def require_valid_bucket_name(value: str) -> str:
    """S3 bucket names: 3 to 63 characters, lower-case letters, digits, dots, hyphens."""
    if not _BUCKET_NAME.match(value):
        raise ValueError(f"'{value}' is not a valid S3 bucket name")
    return value


def require_schedule_expression(value: str) -> str:
    """EventBridge schedules must look like rate(5 minutes) or cron(0 12 * * ? *)."""
    if not _SCHEDULE_EXPRESSION.match(value):
        raise ValueError(f"'{value}' must start with rate( or cron(")
    return value


def require_unique(values: Iterable[str], label: str) -> None:
    """Raise when the same name appears twice in one list of resources."""
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {label}: '{value}'")
        seen.add(value)
