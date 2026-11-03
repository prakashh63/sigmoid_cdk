"""Switches that turn governance features on or off (see docs/feature-flags.md)."""

from __future__ import annotations

from dataclasses import dataclass

from constructs import Node

from sigmoid_cdk.application_constants import CONTEXT_KEY_PREFIX


def _read_bool(node: Node, key: str, default: bool) -> bool:
    raw = node.try_get_context(f"{CONTEXT_KEY_PREFIX}{key}")
    if raw is None:
        return default
    return str(raw).strip().lower() not in {"false", "0", "no", "off"}


@dataclass(frozen=True)
class FeatureFlags:
    """Governance switches. Defaults are the strict, recommended values."""

    compliance_checks: bool = True
    iam_guardrails: bool = True
    permissions_boundary_policy_name: str | None = None

    @classmethod
    def from_node(cls, node: Node) -> FeatureFlags:
        boundary = node.try_get_context(f"{CONTEXT_KEY_PREFIX}permissions-boundary")
        return cls(
            compliance_checks=_read_bool(node, "compliance-checks", True),
            iam_guardrails=_read_bool(node, "iam-guardrails", True),
            permissions_boundary_policy_name=str(boundary) if boundary else None,
        )
