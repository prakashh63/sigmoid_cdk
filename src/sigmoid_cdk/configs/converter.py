"""Turns AppSettings (short form) into WebAppConfig (full form)."""

from sigmoid_cdk.application_constants import API_PATH_PREFIX
from sigmoid_cdk.configs.api_gateway_config import ApiRouteConfig
from sigmoid_cdk.configs.app_settings import AppSettings
from sigmoid_cdk.configs.web_app_config import WebAppConfig


def convert_app_settings(settings: AppSettings) -> WebAppConfig:
    """The single Lambda serves every path below api/ (a proxy route)."""
    proxy_route = ApiRouteConfig(
        path=f"{API_PATH_PREFIX}/{{proxy+}}",
        http_method="ANY",
        lambda_name=settings.lambda_backend.function_name,
    )
    api = settings.api_gateway.model_copy(update={"routes": [proxy_route]})
    return WebAppConfig(
        app_name=settings.app_name,
        environment=settings.environment,
        owner_team=settings.owner_team,
        organization=settings.organization,
        cost_center=settings.cost_center,
        frontend_bucket=settings.s3,
        lambdas=[settings.lambda_backend],
        api_gateways=[api],
    )
