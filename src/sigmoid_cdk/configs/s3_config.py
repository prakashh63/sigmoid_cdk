"""Settings for one S3 bucket."""

from pydantic import BaseModel, ConfigDict, field_validator

from sigmoid_cdk.utilities.validators import require_valid_bucket_name


class S3Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket_name: str
    auto_delete_objects: bool = False  # not allowed for prod

    @field_validator("bucket_name")
    @classmethod
    def _check_bucket_name(cls, value: str) -> str:
        return require_valid_bucket_name(value)
