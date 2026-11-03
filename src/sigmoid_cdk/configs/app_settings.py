"""AppSettings: the short, single-resource form from the original assignment PDF.

Use it when an application has one bucket, one Lambda and one API. The converter turns it into
the full WebAppConfig.
"""

from pydantic import BaseModel, ConfigDict

from sigmoid_cdk.application_constants import DEFAULT_COST_CENTER, DEFAULT_ORGANIZATION
from sigmoid_cdk.application_types import Stage
from sigmoid_cdk.configs.api_gateway_config import ApiGatewayConfig
from sigmoid_cdk.configs.lambda_config import LambdaConfig
from sigmoid_cdk.configs.s3_config import S3Config


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_name: str
    environment: Stage
    owner_team: str
    organization: str = DEFAULT_ORGANIZATION
    cost_center: str = DEFAULT_COST_CENTER
    s3: S3Config
    lambda_backend: LambdaConfig
    api_gateway: ApiGatewayConfig
