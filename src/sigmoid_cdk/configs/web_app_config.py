"""WebAppConfig: the full description of one application deployment."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sigmoid_cdk.application_constants import (
    API_PATH_PREFIX,
    DEFAULT_COST_CENTER,
    DEFAULT_ORGANIZATION,
)
from sigmoid_cdk.application_types import Stage
from sigmoid_cdk.configs.api_gateway_config import ApiGatewayConfig
from sigmoid_cdk.configs.cloudfront_config import CloudFrontConfig
from sigmoid_cdk.configs.lambda_config import LambdaConfig, LambdaLayerConfig
from sigmoid_cdk.configs.messaging_config import EventRuleConfig, QueueConfig
from sigmoid_cdk.configs.s3_config import S3Config
from sigmoid_cdk.utilities.validators import require_kebab_case, require_unique


class WebAppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_name: str
    environment: Stage
    owner_team: str
    organization: str = DEFAULT_ORGANIZATION
    cost_center: str = DEFAULT_COST_CENTER

    frontend_bucket: S3Config
    extra_buckets: list[S3Config] = Field(default_factory=list)
    layers: list[LambdaLayerConfig] = Field(default_factory=list)
    lambdas: list[LambdaConfig] = Field(min_length=1)
    api_gateways: list[ApiGatewayConfig] = Field(default_factory=list)
    queues: list[QueueConfig] = Field(default_factory=list)
    event_rules: list[EventRuleConfig] = Field(default_factory=list)
    cloudfront: CloudFrontConfig = Field(default_factory=CloudFrontConfig)

    @model_validator(mode="after")
    def _check_whole_config(self) -> Self:
        require_kebab_case(self.app_name)
        buckets = [self.frontend_bucket, *self.extra_buckets]
        bucket_names = [b.bucket_name for b in buckets]
        lambda_names = [f.function_name for f in self.lambdas]
        queue_names = [q.queue_name for q in self.queues]
        api_names = [a.api_name for a in self.api_gateways]

        require_unique(bucket_names, "bucket_name")
        require_unique(lambda_names, "function_name")
        require_unique(queue_names, "queue_name")
        require_unique(api_names, "api_name")
        require_unique([r.rule_name for r in self.event_rules], "rule_name")
        require_unique([layer.layer_name for layer in self.layers], "layer_name")

        if self.environment == "prod" and any(b.auto_delete_objects for b in buckets):
            raise ValueError("auto_delete_objects is not allowed in prod")

        layer_names = {layer.layer_name for layer in self.layers}
        for function in self.lambdas:
            self._require_known(
                function.layer_names, layer_names, "layer", function.function_name
            )
            self._require_known(
                function.send_to_queues,
                set(queue_names),
                "queue",
                function.function_name,
            )
            self._require_known(
                function.read_write_buckets,
                set(bucket_names),
                "bucket",
                function.function_name,
            )

        for api in self.api_gateways:
            if not api.routes:
                raise ValueError(f"api '{api.api_name}' needs at least one route")
            self._require_known(
                [r.lambda_name for r in api.routes],
                set(lambda_names),
                "lambda",
                api.api_name,
            )

        for queue in self.queues:
            if queue.consumer_lambda is not None:
                self._require_known(
                    [queue.consumer_lambda],
                    set(lambda_names),
                    "lambda",
                    queue.queue_name,
                )

        for rule in self.event_rules:
            if rule.target_lambda is not None:
                self._require_known(
                    [rule.target_lambda], set(lambda_names), "lambda", rule.rule_name
                )
            if rule.target_queue is not None:
                self._require_known(
                    [rule.target_queue], set(queue_names), "queue", rule.rule_name
                )

        self._check_cloudfront_api(api_names)
        return self

    @staticmethod
    def _require_known(
        wanted: list[str], known: set[str], kind: str, owner: str
    ) -> None:
        unknown = [name for name in wanted if name not in known]
        if unknown:
            raise ValueError(f"'{owner}' refers to unknown {kind}(s): {unknown}")

    def _check_cloudfront_api(self, api_names: list[str]) -> None:
        wanted = self.cloudfront.api_name
        if wanted is not None and wanted not in api_names:
            raise ValueError(
                f"cloudfront.api_name '{wanted}' is not one of {api_names}"
            )
        served = self.cloudfront_api
        if served is None:
            return
        for route in served.routes:
            if route.path != API_PATH_PREFIX and not route.path.startswith(
                f"{API_PATH_PREFIX}/"
            ):
                raise ValueError(
                    f"route '{route.path}' of '{served.api_name}' must start with '{API_PATH_PREFIX}/' "
                    "because CloudFront forwards /api/* to it"
                )

    @property
    def cloudfront_api(self) -> ApiGatewayConfig | None:
        """The API behind CloudFront's /api/* behaviour, or None when there are no APIs."""
        if not self.api_gateways:
            return None
        wanted = self.cloudfront.api_name
        if wanted is None:
            return self.api_gateways[0]
        return next(a for a in self.api_gateways if a.api_name == wanted)
