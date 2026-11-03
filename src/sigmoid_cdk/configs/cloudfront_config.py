"""Settings for the CloudFront distribution."""

from pydantic import BaseModel, ConfigDict

from sigmoid_cdk.application_types import PriceClassName


class CloudFrontConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_name: str | None = None  # which API serves /api/*; default is the first API
    price_class: PriceClassName = "100"
    default_root_object: str = "index.html"
