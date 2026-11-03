"""Fixed values shared across the whole framework."""

MANAGED_BY_TAG_VALUE = "sigmoid-cdk"

TAG_ENVIRONMENT = "Environment"
TAG_OWNER = "Owner"
TAG_COST_CENTER = "CostCenter"
TAG_MANAGED_BY = "ManagedBy"
TAG_APPLICATION = "Application"

SUPPORTED_STAGES = ("dev", "staging", "prod")
SUPPORTED_LAMBDA_RUNTIMES = ("PYTHON_3_11", "PYTHON_3_12", "PYTHON_3_13", "PYTHON_3_14")


DEFAULT_ORGANIZATION = "sigmoid"
DEFAULT_COST_CENTER = "unassigned"

# Every API route that CloudFront forwards must live under this path prefix.
API_PATH_PREFIX = "api"

CONTEXT_KEY_PREFIX = "sigmoid:"
