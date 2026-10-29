import json


def handler(event, context):
    # Runs for every message published to the 'orders' topic.
    print(json.dumps(event))
    return {"processed": True}
