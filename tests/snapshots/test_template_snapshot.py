import json
import re

from aws_cdk.assertions import Template
from syrupy.assertion import SnapshotAssertion


def _stable(template: Template) -> dict:
    """Replace asset hashes so the snapshot only changes when the infrastructure changes."""
    text = json.dumps(template.to_json(), sort_keys=True)
    text = re.sub(r"[0-9a-f]{64}\.zip", "ASSET.zip", text)
    return json.loads(text)


def test_simple_dev_snapshot(
    dev_template: Template, snapshot: SnapshotAssertion
) -> None:
    assert _stable(dev_template) == snapshot


def test_full_dev_snapshot(
    full_template: Template, snapshot: SnapshotAssertion
) -> None:
    assert _stable(full_template) == snapshot
