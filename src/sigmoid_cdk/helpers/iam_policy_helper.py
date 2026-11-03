"""Pure functions that inspect resolved IAM policy documents (no AWS calls)."""

from collections.abc import Mapping
from typing import Any

from sigmoid_cdk.utilities.iam_actions import ALLOWED_WILDCARD_RESOURCE_ACTIONS


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def find_policy_violations(document: Mapping[str, Any]) -> list[str]:
    """Return one message per broken rule. An empty list means the policy is acceptable."""
    violations: list[str] = []
    for statement in _as_list(document.get("Statement")):
        if not isinstance(statement, Mapping) or statement.get("Effect") != "Allow":
            continue
        actions = [a for a in _as_list(statement.get("Action")) if isinstance(a, str)]
        resources = _as_list(statement.get("Resource"))
        for action in actions:
            if action == "*" or action.endswith(":*"):
                violations.append(f"action '{action}' allows every action of a service")
        if "*" in resources:
            not_allowed = [
                a for a in actions if a not in ALLOWED_WILDCARD_RESOURCE_ACTIONS
            ]
            if not_allowed:
                violations.append(f"actions {not_allowed} are allowed on Resource '*'")
    return violations


def find_trust_violations(document: Mapping[str, Any]) -> list[str]:
    """A role must never be assumable by any principal ('*')."""
    violations: list[str] = []
    for statement in _as_list(document.get("Statement")):
        if not isinstance(statement, Mapping) or statement.get("Effect") != "Allow":
            continue
        principal = statement.get("Principal")
        values = (
            _as_list(principal.get("AWS"))
            if isinstance(principal, Mapping)
            else [principal]
        )
        if "*" in values:
            violations.append(
                "trust policy allows any principal ('*') to assume the role"
            )
    return violations
