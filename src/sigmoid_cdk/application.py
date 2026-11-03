"""SigmoidApp: the one-line entry point for developers."""

import os
from typing import Any

import aws_cdk as cdk

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.app_settings import AppSettings
from sigmoid_cdk.configs.converter import convert_app_settings
from sigmoid_cdk.configs.web_app_config import WebAppConfig
from sigmoid_cdk.feature_flags import FeatureFlags
from sigmoid_cdk.helpers.name_helper import to_pascal_case
from sigmoid_cdk.stacks.serverless_web_app_stack import ServerlessWebAppStack


def _default_environment() -> cdk.Environment | None:
    account = os.environ.get("CDK_DEFAULT_ACCOUNT")
    region = os.environ.get("CDK_DEFAULT_REGION")
    return (
        cdk.Environment(account=account, region=region) if account and region else None
    )


class SigmoidApp(cdk.App):
    """A CDK app that already contains the fully configured ServerlessWebAppStack."""

    def __init__(
        self,
        config: WebAppConfig | AppSettings,
        *,
        flags: FeatureFlags | None = None,
        **app_kwargs: Any,
    ) -> None:
        super().__init__(**app_kwargs)
        web_config = (
            convert_app_settings(config) if isinstance(config, AppSettings) else config
        )
        sigmoid_context = SigmoidContext.from_config(web_config)
        self.web_app_stack = ServerlessWebAppStack(
            self,
            f"{to_pascal_case(web_config.app_name)}{to_pascal_case(web_config.environment)}Stack",
            config=web_config,
            context=sigmoid_context,
            flags=flags or FeatureFlags.from_node(self.node),
            env=_default_environment(),
        )
