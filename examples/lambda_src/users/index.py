import json
import os


def handler(event, context):
    user_id = (event.get("pathParameters") or {}).get("id", "0")
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {"id": user_id, "name": f"User {user_id}", "stage": os.environ.get("STAGE")}
        ),
    }
