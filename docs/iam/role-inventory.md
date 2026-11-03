# IAM role inventory

Generate the live list with `cdk synth && python tools/iam_report.py cdk.out`.

| Role | Trusted by | Allowed |
|---|---|---|
| `<app>-<stage>-<function>-role` (one per Lambda) | `lambda.amazonaws.com` | `logs:CreateLogStream`, `logs:PutLogEvents` on its own log group; plus SQS send / S3 read-write only for queues and buckets named in its `LambdaConfig`; SQS consume for its queue |
| API Gateway account logging role (one per stack) | `apigateway.amazonaws.com` | AWS-managed `AmazonAPIGatewayPushToCloudWatchLogs` |
| CDK-created helper roles (e.g. bucket auto-delete, dev only) | Lambda | Created by CDK itself |
