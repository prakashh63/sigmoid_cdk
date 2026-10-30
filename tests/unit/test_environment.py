from collections.abc import Callable

import aws_cdk as cdk
import pytest

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import AwsEnvConfig, WebAppConfig
from sigmoid_cdk.stacks._environment import resolve_environment

MakeConfig = Callable[..., WebAppConfig]


def synth_stack(config: WebAppConfig, **kwargs: object) -> ServerlessWebAppStack:
    return ServerlessWebAppStack(cdk.App(), "S", config=config, enable_compliance=False, **kwargs)


def test_nothing_known_stays_environment_agnostic(make_config: MakeConfig) -> None:
    stack = synth_stack(make_config())
    assert cdk.Token.is_unresolved(stack.account)
    assert cdk.Token.is_unresolved(stack.region)


def test_cli_defaults_are_used(make_config: MakeConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "ap-south-1")
    stack = synth_stack(make_config())
    assert stack.account == "123456789012"
    assert stack.region == "ap-south-1"


def test_config_overrides_cli_defaults(
    make_config: MakeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "ap-south-1")
    stack = synth_stack(make_config(aws={"region": "eu-west-1"}))
    assert stack.region == "eu-west-1"  # from the config
    assert stack.account == "123456789012"  # field not set in config -> CLI default


def test_explicit_env_wins_over_everything(
    make_config: MakeConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    config = make_config(aws={"account": "222222222222", "region": "ap-south-1"})
    stack = synth_stack(config, env=cdk.Environment(account="111111111111", region="us-east-1"))
    assert stack.account == "111111111111"
    assert stack.region == "us-east-1"


def test_empty_variables_count_as_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "")
    assert resolve_environment(None) is None


def test_region_only_is_enough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDK_DEFAULT_REGION", "ap-south-1")
    env = resolve_environment(None)
    assert env is not None
    assert env.region == "ap-south-1"
    assert env.account is None


def test_aws_config_without_cli_defaults() -> None:
    env = resolve_environment(AwsEnvConfig(account="123456789012", region="ap-south-1"))
    assert env is not None
    assert (env.account, env.region) == ("123456789012", "ap-south-1")
