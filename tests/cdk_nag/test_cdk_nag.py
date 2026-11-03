from aws_cdk.assertions import Annotations, Match

from tests.conftest import synth
from tests.fixtures.sample_configs import full_config, simple_settings


def _nag_errors(config: object) -> list[object]:
    app, _ = synth(config)
    return Annotations.from_stack(app.web_app_stack).find_error(
        "*",
        Match.string_like_regexp(r"AwsSolutions-.*|\[sigmoid-cdk IAM guardrail\].*"),
    )


def test_simple_stack_has_no_unacknowledged_findings() -> None:
    assert _nag_errors(simple_settings("prod")) == []


def test_full_stack_has_no_unacknowledged_findings() -> None:
    assert _nag_errors(full_config("prod")) == []
