import pytest
from pydantic import ValidationError

from sigmoid_cdk.configs import (
    ApiGatewayConfig,
    LambdaConfig,
    QueueConfig,
    S3Config,
    WebAppConfig,
    convert_app_settings,
)
from tests.fixtures.sample_configs import LAMBDA_SRC, full_config, simple_settings


def test_memory_is_limited() -> None:
    with pytest.raises(ValidationError):
        LambdaConfig(
            function_name="too-big", entry_point_dir=LAMBDA_SRC, memory_mb=4096
        )


def test_runtime_must_be_supported() -> None:
    with pytest.raises(ValidationError):
        LambdaConfig(
            function_name="old-one", entry_point_dir=LAMBDA_SRC, runtime="PYTHON_3_6"
        )


def test_bucket_name_is_validated() -> None:
    with pytest.raises(ValidationError):
        S3Config(bucket_name="Bad_Name")


def test_prod_rejects_auto_delete() -> None:
    config = full_config("prod").model_dump()
    config["frontend_bucket"]["auto_delete_objects"] = True
    with pytest.raises(ValidationError):
        WebAppConfig(**config)


def test_unknown_lambda_reference_is_rejected() -> None:
    config = full_config().model_dump()
    config["queues"] = [
        QueueConfig(queue_name="q-one", consumer_lambda="missing-fn").model_dump()
    ]
    with pytest.raises(ValidationError):
        WebAppConfig(**config)


def test_cloudfront_api_routes_need_api_prefix() -> None:
    config = full_config().model_dump()
    config["api_gateways"][0]["routes"][0]["path"] = "orders"
    with pytest.raises(ValidationError):
        WebAppConfig(**config)


def test_converter_creates_proxy_route() -> None:
    web = convert_app_settings(simple_settings())
    route = web.api_gateways[0].routes[0]
    assert (route.path, route.http_method) == ("api/{proxy+}", "ANY")
    assert route.lambda_name == "portal-api-handler"


def test_api_defaults() -> None:
    api = ApiGatewayConfig()
    assert (api.stage_name, api.enable_cors, api.rate_limit, api.burst_limit) == (
        "prod",
        True,
        1000,
        500,
    )
