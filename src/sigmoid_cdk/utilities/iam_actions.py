"""IAM action lists used by constructs and by the IAM guardrail."""

LOG_WRITE_ACTIONS = ("logs:CreateLogStream", "logs:PutLogEvents")

# Actions AWS only supports with Resource "*". The guardrail allows these and nothing else.
ALLOWED_WILDCARD_RESOURCE_ACTIONS = frozenset(
    {
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
    }
)
