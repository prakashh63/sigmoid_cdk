"""Prints every IAM role, its trust, actions and resources from synthesized templates.

Usage: python tools/iam_report.py [cdk.out]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _short(value: Any) -> str:
    return json.dumps(value, sort_keys=True) if not isinstance(value, str) else value


def report_template(template: dict[str, Any]) -> list[str]:
    resources: dict[str, Any] = template.get("Resources", {})
    lines: list[str] = []
    for logical_id, resource in resources.items():
        if resource["Type"] != "AWS::IAM::Role":
            continue
        props = resource["Properties"]
        lines.append(f"ROLE {logical_id} ({props.get('RoleName', 'generated name')})")
        for statement in _as_list(props["AssumeRolePolicyDocument"]["Statement"]):
            lines.append(f"  trust: {_short(statement.get('Principal'))}")
        for managed in _as_list(props.get("ManagedPolicyArns")):
            lines.append(f"  managed policy: {_short(managed)}")
        for other in resources.values():
            if other["Type"] != "AWS::IAM::Policy":
                continue
            attached = [r.get("Ref") for r in other["Properties"].get("Roles", [])]
            if logical_id not in attached:
                continue
            for statement in _as_list(
                other["Properties"]["PolicyDocument"]["Statement"]
            ):
                actions = ", ".join(_as_list(statement.get("Action")))
                lines.append(f"  allow [{actions}]")
                for resource_arn in _as_list(statement.get("Resource")):
                    lines.append(f"      on {_short(resource_arn)}")
    return lines


def main(argv: list[str]) -> int:
    out_dir = Path(argv[1]) if len(argv) > 1 else Path("cdk.out")
    templates = sorted(out_dir.glob("*.template.json"))
    if not templates:
        print(f"no templates found in {out_dir}; run `cdk synth` first")
        return 1
    for path in templates:
        print(f"# {path.name}")
        print("\n".join(report_template(json.loads(path.read_text(encoding="utf-8")))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
