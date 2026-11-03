import pytest
from aws_cdk.assertions import Template

from sigmoid_cdk import SigmoidApp
from sigmoid_cdk.configs import WebAppConfig
from tests.fixtures.sample_configs import full_config, simple_settings


def synth(config: object) -> tuple[SigmoidApp, Template]:
    app = SigmoidApp(config, context={"aws:cdk:bundling-stacks": []})  # type: ignore[arg-type]
    return app, Template.from_stack(app.web_app_stack)


@pytest.fixture
def prod_template() -> Template:
    return synth(simple_settings("prod"))[1]


@pytest.fixture
def dev_template() -> Template:
    return synth(simple_settings("dev"))[1]


@pytest.fixture
def full_template() -> Template:
    config: WebAppConfig = full_config("dev")
    return synth(config)[1]
