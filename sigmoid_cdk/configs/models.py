"""Pydantic schemas: validate user input before any AWS resource is created."""

import re
from collections.abc import Iterable
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

ALLOWED_RUNTIMES = (
    "PYTHON_3_10",
    "PYTHON_3_11",
    "PYTHON_3_12",
    "PYTHON_3_13",
    "PYTHON_3_14",
)
DEFAULT_RUNTIME = "PYTHON_3_14"

_SCHEDULE_RE = re.compile(r"^(rate|cron)\(.+\)$")

# Keys of the buckets / topics / lambdas maps become construct IDs and env var names,
# so they are restricted to lowercase letters, digits and hyphens.
ResourceKey = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$", max_length=40)]

BucketAccess = Literal["read", "write", "read_write"]

# Old single-resource keys (0.1 / 0.2 and the original assignment sample).
_LEGACY_KEYS = ("s3", "lambda_backend", "triggers")


class _Strict(BaseModel):
    """Base class: unknown fields are rejected, so a typo never passes silently."""

    model_config = ConfigDict(extra="forbid")


class S3Config(_Strict):
    """Private bucket. Optionally served through CloudFront."""

    bucket_name: str = Field(min_length=3, max_length=63, pattern=r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$")
    auto_delete_objects: bool = False
    # Exactly one bucket may be the CloudFront default origin (serves '/').
    cdn_default: bool = False
    # Extra CloudFront path served from this bucket, e.g. '/assets/*'.
    cdn_path: str | None = Field(
        default=None, pattern=r"^/[A-Za-z0-9._~-]+(/[A-Za-z0-9._~-]+)*/\*$"
    )


class TopicConfig(_Strict):
    """SNS topic (encrypted, SSL only). Lambdas subscribe to it by its key."""

    topic_name: str = Field(min_length=1, max_length=256, pattern=r"^[A-Za-z0-9_-]+$")


class ScheduleTriggerConfig(_Strict):
    """EventBridge schedule, e.g. 'rate(5 minutes)' or 'cron(0 12 * * ? *)'."""

    expression: str

    @field_validator("expression")
    @classmethod
    def check_expression(cls, value: str) -> str:
        if not _SCHEDULE_RE.match(value):
            raise ValueError("expression must look like 'rate(5 minutes)' or 'cron(0 12 * * ? *)'")
        return value


class EventRuleTriggerConfig(_Strict):
    """EventBridge rule that matches events by source (and optionally detail-type)."""

    source: list[str] = Field(min_length=1)
    detail_type: list[str] = Field(default_factory=list)
    event_bus_name: str | None = None  # None means the account's default event bus


class TriggerConfig(_Strict):
    """Event sources of ONE Lambda. Leave everything empty for none."""

    schedule: ScheduleTriggerConfig | None = None
    event_rule: EventRuleTriggerConfig | None = None
    sns: list[ResourceKey] = Field(default_factory=list)  # keys from the top-level `topics`


class LambdaConfig(_Strict):
    """One Lambda function. Works for web backends and for worker functions."""

    function_name: str
    entry_point_dir: str  # relative paths are resolved from the config file's folder
    handler: str = "index.handler"
    runtime: str = DEFAULT_RUNTIME
    memory_mb: int = Field(default=512, ge=128, le=3072)
    timeout_seconds: int = Field(default=30, ge=1, le=900)
    environment_vars: dict[str, str] = Field(default_factory=dict)
    # bucket key -> access level. The bucket name is injected as BUCKET_<KEY>.
    bucket_access: dict[ResourceKey, BucketAccess] = Field(default_factory=dict)
    triggers: TriggerConfig = Field(default_factory=TriggerConfig)

    @field_validator("runtime")
    @classmethod
    def check_runtime(cls, value: str) -> str:
        if value not in ALLOWED_RUNTIMES:
            raise ValueError(f"runtime must be one of {list(ALLOWED_RUNTIMES)}")
        return value


class RouteConfig(_Strict):
    """One API route: this path and everything below it goes to one Lambda."""

    path: str = Field(pattern=r"^/([A-Za-z0-9._~-]+(/[A-Za-z0-9._~-]+)*)?$")
    function: ResourceKey  # key from the top-level `lambdas`


class ApiGatewayConfig(_Strict):
    """API Gateway in front of the Lambdas. Set enable_proxy=false for worker-only stacks."""

    enable_proxy: bool = True
    stage_name: str = Field(default="prod", pattern=r"^[A-Za-z0-9_-]+$")
    enable_cors: bool = True
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    rate_limit: int = Field(default=1000, gt=0)
    burst_limit: int = Field(default=500, gt=0)
    # Required when there is more than one Lambda. With one Lambda and no routes,
    # everything ('/') goes to that Lambda.
    routes: list[RouteConfig] = Field(default_factory=list)


def _duplicates(label: str, values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        (dupes if value in seen else seen).add(value)
    return [f"duplicate {label}: {value!r}" for value in sorted(dupes)]


def _as_dict(value: Any) -> dict[str, Any]:
    return value.model_dump() if isinstance(value, BaseModel) else dict(value)


class AwsEnvConfig(_Strict):
    """Optional override. Leave a field out to use the CLI's account / region."""

    account: str | None = Field(default=None, pattern=r"^\d{12}$")  # quote it in YAML
    region: str | None = Field(default=None, pattern=r"^[a-z]{2}(-[a-z]+)+-\d$")


class WebAppConfig(_Strict):
    """Top-level configuration for ServerlessWebAppStack."""

    app_name: str = Field(min_length=1)
    environment: Literal["dev", "staging", "prod"]
    owner_team: str = Field(min_length=1)
    cost_center: str | None = None
    encrypt_logs: bool = True
    aws: AwsEnvConfig | None = None
    buckets: dict[ResourceKey, S3Config] = Field(default_factory=dict)
    topics: dict[ResourceKey, TopicConfig] = Field(default_factory=dict)
    lambdas: dict[ResourceKey, LambdaConfig] = Field(min_length=1)
    api_gateway: ApiGatewayConfig = Field(default_factory=ApiGatewayConfig)

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy_keys(cls, data: Any) -> Any:
        """Accept the old `s3`, `lambda_backend`, `triggers` keys (single-resource config)."""
        if not isinstance(data, dict) or not any(key in data for key in _LEGACY_KEYS):
            return data
        if any(key in data for key in ("buckets", "lambdas", "topics")):
            raise ValueError(
                "Do not mix the old keys (s3, lambda_backend, triggers) "
                "with buckets / lambdas / topics."
            )
        upgraded: dict[str, Any] = {k: v for k, v in data.items() if k not in _LEGACY_KEYS}
        if data.get("s3") is not None:
            upgraded["buckets"] = {"web": {**_as_dict(data["s3"]), "cdn_default": True}}
        if data.get("lambda_backend") is not None:
            function = _as_dict(data["lambda_backend"])
            if data.get("triggers") is not None:
                triggers = _as_dict(data["triggers"])
                if isinstance(triggers.get("sns"), dict):  # old style: topic defined inline
                    upgraded["topics"] = {"default": triggers["sns"]}
                    triggers["sns"] = ["default"]
                function["triggers"] = triggers
            upgraded["lambdas"] = {"backend": function}
        return upgraded

    @model_validator(mode="after")
    def _cross_check(self) -> "WebAppConfig":
        errors: list[str] = []
        api = self.api_gateway

        errors += _duplicates("function_name", (f.function_name for f in self.lambdas.values()))
        errors += _duplicates("bucket_name", (b.bucket_name for b in self.buckets.values()))
        errors += _duplicates("topic_name", (t.topic_name for t in self.topics.values()))

        for key, function in self.lambdas.items():
            for bucket_key in function.bucket_access:
                if bucket_key not in self.buckets:
                    errors.append(
                        f"lambda '{key}': bucket_access names unknown bucket '{bucket_key}'"
                    )
            for topic_key in function.triggers.sns:
                if topic_key not in self.topics:
                    errors.append(f"lambda '{key}': sns trigger names unknown topic '{topic_key}'")

        # API routes
        if api.routes and not api.enable_proxy:
            errors.append("api_gateway.routes is set but api_gateway.enable_proxy is false")
        if api.enable_proxy and not api.routes and len(self.lambdas) > 1:
            errors.append(
                "api_gateway.routes is required when there is more than one Lambda "
                "(or set api_gateway.enable_proxy: false for worker-only stacks)"
            )
        errors += _duplicates("route path", (route.path for route in api.routes))
        for route in api.routes:
            if route.function not in self.lambdas:
                errors.append(f"route '{route.path}' targets unknown Lambda '{route.function}'")

        # CloudFront
        defaults = [key for key, bucket in self.buckets.items() if bucket.cdn_default]
        if len(defaults) > 1:
            errors.append(f"only one bucket can have cdn_default: true (found {defaults})")
        errors += _duplicates(
            "cdn_path", (b.cdn_path for b in self.buckets.values() if b.cdn_path is not None)
        )
        for key, bucket in self.buckets.items():
            if bucket.cdn_default and bucket.cdn_path:
                errors.append(f"bucket '{key}': cdn_default and cdn_path cannot be combined")
            if bucket.cdn_path and not defaults:
                errors.append(f"bucket '{key}': cdn_path needs one bucket with cdn_default: true")
            if bucket.cdn_path == "/api/*":
                errors.append(f"bucket '{key}': '/api/*' is reserved for the API")
        if defaults and api.enable_proxy:
            for route in api.routes:
                if route.path != "/" and not route.path.startswith("/api/"):
                    errors.append(
                        f"route '{route.path}' must start with /api/ because CloudFront "
                        "only forwards /api/* to the API"
                    )

        if errors:
            raise ValueError("; ".join(errors))
        return self

    def effective_routes(self) -> list[RouteConfig]:
        """The routes to build: none without API, '/' -> the only Lambda when none are given."""
        if not self.api_gateway.enable_proxy:
            return []
        if self.api_gateway.routes:
            return list(self.api_gateway.routes)
        only = next(iter(self.lambdas))  # validated: exactly one Lambda here
        return [RouteConfig(path="/", function=only)]
