import json
import os


def handler(event, context):
    bucket = os.environ["BUCKET_UPLOADS"]  # injected because of bucket_access
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {"service": "users", "uploads_bucket": bucket, "path": event.get("path")}
        ),
    }
