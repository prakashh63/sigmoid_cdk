# Changelog

## 0.3.0
- **Renamed** the package from `company_cdk` to `sigmoid_cdk` (`ManagedBy` tag is now `sigmoid_cdk`).
- **Multiple resources in one stack**: `lambdas`, `buckets` and `topics` are maps keyed by a
  logical name. Any number of each is allowed.
- Each Lambda has its own role, log group, memory, timeout, runtime and env vars; all share one
  KMS log key.
- Per-Lambda `bucket_access` (`read`, `write`, `read_write`): least-privilege S3 actions on that
  bucket only, bucket name injected as `BUCKET_<KEY>`.
- Per-Lambda `triggers`. SNS topics are defined once under `topics` and can be shared by several
  Lambdas.
- API Gateway `routes`: one API, each path prefix goes to its own Lambda.
- CloudFront: one default bucket (`cdn_default`) and extra buckets on their own path (`cdn_path`).
- Cross-checks at load time with clear errors (unknown names, duplicates, bad CDN setup, routes).
- The old single-resource keys (`s3`, `lambda_backend`, `triggers`) are still accepted and
  converted automatically.
- New `examples/multi`, new multi-resource tests and snapshot.
- Outputs are now named per resource (for example `UsersFunctionName`, `UploadsBucketName`).
- Breaking: construct IDs and output names changed, so a stack deployed with 0.2.0 would see
  resources replaced.

## 0.2.0
- Default Lambda runtime is now `PYTHON_3_14` (satisfies cdk-nag AwsSolutions-L1).
- CloudWatch log groups are encrypted with a customer-managed KMS key (`encrypt_logs`, default on).
- API Gateway proxy is optional (`api_gateway.enable_proxy`), so worker Lambdas need no API.
- `s3` is optional: API-only and worker-only stacks are supported.
- New `SecureLambda` construct that works for any use case.
- Event triggers: EventBridge schedule, EventBridge event pattern, SNS topic subscription.
- Configurable CORS origins and Lambda timeout.
- `load_config` gives clear errors for missing or empty files and resolves the Lambda code
  folder relative to the config file.

## 0.1.0
- Config schemas (Pydantic) and YAML loader.
- SecureBucket, ServerlessBackend, WebDistribution constructs.
- ServerlessWebAppStack with auto-tagging and cdk-nag (AwsSolutionsChecks).
- Unit and snapshot tests, example apps.
