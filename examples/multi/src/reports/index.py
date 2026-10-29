import json
import os


def handler(event, context):
    # Called by API Gateway (/api/reports) and by the daily schedule.
    bucket = os.environ["BUCKET_UPLOADS"]
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"service": "reports", "reads_from": bucket}),
    }
