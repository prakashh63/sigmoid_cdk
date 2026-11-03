# Security defaults

## Locked (cannot be changed through config)
| Area | Rule |
|---|---|
| S3 | Block all public access, encryption at rest, HTTPS-only policy, ACLs disabled |
| S3 | Frontend reachable only through CloudFront Origin Access Control |
| CloudFront | Viewers redirected to HTTPS |
| Logs | Every log group encrypted with KMS (key rotation on) |
| API Gateway | Throttling on, request validation on, access logs on, regional endpoint |
| Lambda | One role per function; only writes its own log group; no AWS-managed policies |
| SQS | Encrypted, HTTPS-only, dead-letter queue |
| Tags | Environment, Owner, CostCenter, ManagedBy, Application on every taggable resource |
| IAM | No bare `*` action or resource; no role assumable by `*` |

## Adjustable
| Setting | Default | Limits |
|---|---|---|
| `memory_mb` | 512 | 128-3072 |
| `timeout_seconds` | 30 | 1-900 |
| `rate_limit` / `burst_limit` | 1000 / 500 | at least 1 |
| `enable_cors` / `cors_allowed_origins` | on / `["*"]` | restrict origins for real apps |
| Log retention | 7 / 30 / 90 days (dev / staging / prod) | by stage only |
| Bucket versioning | prod only | by stage only |
| `auto_delete_objects` | false | forbidden in prod |
| CloudFront price class | 100 | 100, 200, ALL |
