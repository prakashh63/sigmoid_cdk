import json
import os
import time
import uuid

import boto3

s3 = boto3.client("s3")
BUCKET = next(v for k, v in os.environ.items() if k.startswith("BUCKET_NAME_"))


def _reply(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    if event["httpMethod"] == "POST":
        raw = event.get("body") or "{}"
        if len(raw) > 1000:
            return _reply(413, {"error": "body too large"})
        order = {
            "id": uuid.uuid4().hex[:8],
            "created": int(time.time()),
            **json.loads(raw),
        }
        s3.put_object(
            Bucket=BUCKET, Key=f"orders/{order['id']}.json", Body=json.dumps(order)
        )
        return _reply(201, order)
    listing = s3.list_objects_v2(Bucket=BUCKET, Prefix="orders/", MaxKeys=20)
    orders = [
        json.loads(s3.get_object(Bucket=BUCKET, Key=o["Key"])["Body"].read())
        for o in listing.get("Contents", [])
    ]
    return _reply(200, {"count": len(orders), "orders": orders})
