"""Settings for one API Gateway REST API and its routes."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sigmoid_cdk.utilities.validators import require_kebab_case

_HTTP_METHODS = {"ANY", "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}


class ApiRouteConfig(BaseModel):
    """One route, for example path 'api/orders/{order_id}' + GET -> a Lambda function."""

    model_config = ConfigDict(extra="forbid")

    path: str
    http_method: str = "ANY"
    lambda_name: str  # function_name of the Lambda that serves the route

    @field_validator("path")
    @classmethod
    def _check_path(cls, value: str) -> str:
        if value.startswith("/") or not value:
            raise ValueError("route path must not be empty or start with '/'")
        return value

    @field_validator("http_method")
    @classmethod
    def _check_method(cls, value: str) -> str:
        if value not in _HTTP_METHODS:
            raise ValueError(f"http_method must be one of {sorted(_HTTP_METHODS)}")
        return value


class ApiGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_name: str = "web-api"
    stage_name: str = "prod"
    enable_cors: bool = True
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit: int = Field(default=1000, ge=1)
    burst_limit: int = Field(default=500, ge=1)
    routes: list[ApiRouteConfig] = Field(default_factory=list)

    @field_validator("api_name")
    @classmethod
    def _check_api_name(cls, value: str) -> str:
        return require_kebab_case(value)
