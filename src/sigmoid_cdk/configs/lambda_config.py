"""Settings for Lambda functions and Lambda layers."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sigmoid_cdk.application_constants import SUPPORTED_LAMBDA_RUNTIMES
from sigmoid_cdk.utilities.validators import require_kebab_case


class LambdaLayerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layer_name: str
    source_dir: str

    @field_validator("layer_name")
    @classmethod
    def _check_layer_name(cls, value: str) -> str:
        return require_kebab_case(value)


class LambdaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function_name: str
    entry_point_dir: str
    handler: str = "index.handler"
    runtime: str = "PYTHON_3_14"
    memory_mb: int = Field(default=512, ge=128, le=3072)
    timeout_seconds: int = Field(default=30, ge=1, le=900)
    environment_vars: dict[str, str] = Field(default_factory=dict)
    layer_names: list[str] = Field(default_factory=list)
    send_to_queues: list[str] = Field(default_factory=list)  # queue_name values
    read_write_buckets: list[str] = Field(default_factory=list)  # bucket_name values

    @field_validator("function_name")
    @classmethod
    def _check_function_name(cls, value: str) -> str:
        return require_kebab_case(value)

    @field_validator("runtime")
    @classmethod
    def _check_runtime(cls, value: str) -> str:
        if value not in SUPPORTED_LAMBDA_RUNTIMES:
            raise ValueError(f"runtime must be one of {SUPPORTED_LAMBDA_RUNTIMES}")
        return value
