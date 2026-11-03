# Getting started

1. Install: `pip install -e ".[dev]"` and `npm install -g aws-cdk`.
2. Run `pytest` - all tests pass without AWS credentials (nothing is deployed).
3. Run `cdk synth` - writes CloudFormation to `cdk.out/`. Synthesis stops if cdk-nag finds an
   unacknowledged security problem.
4. Deploy (needs AWS credentials): `cdk bootstrap` once per account/region, then `cdk deploy`.

## Short form: AppSettings
One bucket, one Lambda, one API. See `examples/app.py`. The Lambda serves every path under `api/`.

## Full form: WebAppConfig
```python
WebAppConfig(
    app_name="orders-app",
    environment="dev",
    owner_team="orders-team",
    frontend_bucket=S3Config(bucket_name="orders-web-dev"),
    lambdas=[
        LambdaConfig(
            function_name="orders-api",
            entry_point_dir="src/orders",
            send_to_queues=["order-events"],
        ),
        LambdaConfig(function_name="order-worker", entry_point_dir="src/worker"),
    ],
    api_gateways=[
        ApiGatewayConfig(
            api_name="orders-gateway",
            routes=[
                ApiRouteConfig(
                    path="api/orders", http_method="GET", lambda_name="orders-api"
                )
            ],
        )
    ],
    queues=[QueueConfig(queue_name="order-events", consumer_lambda="order-worker")],
    event_rules=[
        EventRuleConfig(
            rule_name="nightly",
            schedule_expression="rate(1 day)",
            target_lambda="order-worker",
        )
    ],
)
app = SigmoidApp(config)
app.synth()
```
Wrong names (a route pointing to a missing Lambda, a prod bucket with auto-delete) fail at once with a
clear message, before any AWS call.

## Environment variables the framework adds to a Lambda
`STAGE`, `QUEUE_URL_<QUEUE_NAME>` for each `send_to_queues` entry and `BUCKET_NAME_<BUCKET_NAME>` for
each `read_write_buckets` entry.
