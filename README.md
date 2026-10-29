# sigmoid_cdk

Reusable internal Python package that turns a short YAML (or Python) config into a secure
AWS stack built with the AWS CDK. One stack can hold **any number of Lambdas, S3 buckets and SNS
topics**.

| Shape | Config | Creates |
| --- | --- | --- |
| Web app | a bucket with `cdn_default: true` + one Lambda | S3 + CloudFront (OAC) + API Gateway + Lambda |
| API only | no bucket with `cdn_default` | API Gateway + Lambda(s) |
| Worker | `api_gateway.enable_proxy: false` (+ `triggers`) | Lambda(s) triggered by EventBridge / SNS |
| Multi | several `lambdas`, `buckets`, `topics` + `api_gateway.routes` | all of the above in one stack |

## What every stack gets by default

| Area | Behaviour |
| --- | --- |
| S3 | All public access blocked, S3-managed encryption, SSL enforced, versioning in prod |
| CloudFront | Origin Access Control to every bucket it serves, `/api/*` routed to API Gateway, HTTPS redirect |
| API Gateway | One API, a route table to different Lambdas, CORS, throttling, access logs, request validator |
| Lambda | One role and one log group per function; the role can only write its own logs plus the buckets you grant |
| Logs | Retention 7 days (dev), 30 days (staging), 90 days (prod); one shared customer-managed KMS key with rotation |
| SNS | Encrypted (AWS-managed key), SSL-only publishing |
| Tags | `Environment`, `Owner`, `ManagedBy=sigmoid_cdk`, optional `CostCenter` on every taggable resource |
| Compliance | cdk-nag `AwsSolutionsChecks`; a violation makes `cdk synth` fail (exit code 1) |

## Install

Requirements: Python 3.12+, Node.js and the CDK CLI (`npm install -g aws-cdk`).

```bash
# from a git repository
pip install "git+https://github.com/prakashh63/sigmoid_cdk.git@v0.3.0"

# or from a built wheel
pip install sigmoid_cdk-0.3.0-py3-none-any.whl
```

## Quick start (web app)

`config.yaml`:

```yaml
app_name: customer-portal
environment: dev            # dev | staging | prod
owner_team: frontend-devs
cost_center: CC-1024        # optional
buckets:
  web:
    bucket_name: cust-portal-web-assets-dev
    cdn_default: true
lambdas:
  backend:
    function_name: portal-api-handler
    entry_point_dir: src/backend_lambda   # relative to config.yaml
    memory_mb: 1024
api_gateway:
  stage_name: v1
  rate_limit: 2000
```

`app.py` and `cdk.json` (`{ "app": "python app.py" }`):

```python
from pathlib import Path

import aws_cdk as cdk

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import load_config

app = cdk.App()
config = load_config(Path(__file__).parent / "config.yaml")
ServerlessWebAppStack(app, "CustomerPortalStack", config=config)
app.synth()
```

```bash
cdk synth      # builds the template and runs cdk-nag
cdk deploy     # optional, needs an AWS account
```

With one Lambda and no `routes`, every path of the API goes to that Lambda.

## Several Lambdas, buckets and topics

`buckets`, `topics` and `lambdas` are maps. The key (for example `users`) is a stable logical
name: lowercase letters, digits and `-`. It becomes the construct ID, the output name and the env
var name, so renaming a key later replaces that resource.

```yaml
buckets:
  website: { bucket_name: portal-web-dev, cdn_default: true }      # CloudFront '/'
  assets:  { bucket_name: portal-assets-dev, cdn_path: /assets/* } # CloudFront '/assets/*'
  uploads: { bucket_name: portal-uploads-dev }                     # private data bucket

topics:
  orders: { topic_name: portal-orders }

lambdas:
  users:
    function_name: users-fn
    entry_point_dir: src/users
    bucket_access: { uploads: read_write }     # env var BUCKET_UPLOADS is injected
  reports:
    function_name: reports-fn
    entry_point_dir: src/reports
    bucket_access: { uploads: read }
    triggers:
      schedule: { expression: rate(1 day) }
  order-worker:
    function_name: order-worker
    entry_point_dir: src/worker
    triggers:
      sns: [orders]                            # keys from `topics`; several Lambdas may share one

api_gateway:
  routes:                                      # required when there is more than one Lambda
    - { path: /api/users, function: users }    # this path and everything below it
    - { path: /api/reports, function: reports }
```

Rules the loader enforces (with clear error messages):

- A route, `bucket_access` entry or SNS trigger must name something that exists.
- `function_name`, `bucket_name`, `topic_name`, route paths and `cdn_path` must be unique.
- At most one bucket has `cdn_default: true`; `cdn_path` needs a `cdn_default` bucket and cannot
  be `/api/*`.
- More than one Lambda with the API enabled needs `routes`.
- When CloudFront is used, routes must start with `/api/` (CloudFront only forwards `/api/*`).
- Objects served from a `cdn_path` bucket must be stored under that prefix
  (`/assets/logo.png` reads the key `assets/logo.png`).

Access levels: `read` = `s3:GetObject` + `s3:ListBucket`; `write` = `s3:PutObject` +
`s3:AbortMultipartUpload`; `read_write` = both plus `s3:DeleteObject`. Only on the named bucket.

### Old single-resource keys

`s3`, `lambda_backend` and `triggers` (the original assignment form) still work. They are
converted to `buckets: {web: ...cdn_default}` and `lambdas: {backend: ...}`. Do not mix old and
new keys in one config.

## Worker Lambda (no API Gateway)

```yaml
app_name: order-worker
environment: dev
owner_team: backend-devs
topics:
  orders: { topic_name: order-worker-topic }
lambdas:
  worker:
    function_name: order-worker
    entry_point_dir: src/worker_lambda
    triggers:
      schedule: { expression: rate(1 hour) }      # or cron(0 12 * * ? *)
      event_rule:
        source: [orders.service]
        detail_type: [Order Created]              # optional
        event_bus_name: my-bus                    # optional, default bus when omitted
      sns: [orders]
api_gateway:
  enable_proxy: false
```

Using only the Lambda in your own stack:

```python
from sigmoid_cdk.constructs import SecureLambda
```

## Configuration reference

| Field | Default | Rule |
| --- | --- | --- |
| `app_name`, `owner_team` | required | non-empty |
| `environment` | required | `dev`, `staging` or `prod` |
| `cost_center` | none | adds the `CostCenter` tag |
| `encrypt_logs` | `true` | one shared KMS key for all log groups (small monthly cost); `false` skips it |
| `buckets.<key>.bucket_name` | required | 3 to 63 chars, lowercase, digits, `.` and `-` |
| `buckets.<key>.auto_delete_objects` | `false` | ignored in prod |
| `buckets.<key>.cdn_default` | `false` | at most one bucket; served at `/` |
| `buckets.<key>.cdn_path` | none | for example `/assets/*` |
| `topics.<key>.topic_name` | required | letters, digits, `_`, `-` |
| `lambdas.<key>` | at least one | |
| `lambdas.<key>.function_name`, `entry_point_dir` | required | folder must exist |
| `lambdas.<key>.handler` | `index.handler` | |
| `lambdas.<key>.runtime` | `PYTHON_3_14` | `PYTHON_3_10` to `PYTHON_3_14` |
| `lambdas.<key>.memory_mb` | 512 | 128 to 3072 |
| `lambdas.<key>.timeout_seconds` | 30 | 1 to 900 |
| `lambdas.<key>.environment_vars` | `{}` | |
| `lambdas.<key>.bucket_access` | `{}` | bucket key to `read`, `write` or `read_write` |
| `lambdas.<key>.triggers.schedule.expression` | none | `rate(...)` or `cron(...)` |
| `lambdas.<key>.triggers.event_rule.source` | none | at least one source |
| `lambdas.<key>.triggers.sns` | `[]` | list of topic keys |
| `api_gateway.enable_proxy` | `true` | `false` creates no API Gateway |
| `api_gateway.routes` | `[]` | list of `{path, function}` |
| `api_gateway.stage_name` | `prod` | letters, digits, `_`, `-` |
| `api_gateway.enable_cors` | `true` | |
| `api_gateway.cors_allowed_origins` | `["*"]` | restrict this in production |
| `api_gateway.rate_limit` / `burst_limit` | 1000 / 500 | greater than 0 |

Unknown fields and invalid values fail when the config is loaded, before any AWS resource exists.

## Stack outputs

`SiteUrl` (with CloudFront), `<Key>BucketName`, `<Key>FunctionName`, `<Key>TopicArn`, for example
`UploadsBucketName`, `OrderWorkerFunctionName`.

## cdk-nag findings

Findings fixed in code: runtime (L1), request validator (APIG2), stage logging (APIG6),
log encryption, SNS encryption and SSL.

Findings acknowledged with a written reason (see the constructs):

| Rule | Reason |
| --- | --- |
| S1, CFR3 | Access logging needs a dedicated log bucket (tracked improvement) |
| APIG4, COG4 | No authorizer in the current spec; add one per application |
| APIG3, CFR2 | WAF is a paid add-on; enable per application |
| CFR1 | Geo restriction is a per-application business decision |
| CFR4 | Default CloudFront certificate; a TLS floor needs a custom domain |
| IAM4 | AWS-managed service role API Gateway uses to push logs |
| IAM5 | Only on a Lambda role that has `bucket_access`: object access needs `<bucket>/*` on the granted bucket |

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/verify.py      # ruff, mypy, pytest, cdk synth for all three examples
```

Individual commands:

```bash
pytest -q
pytest tests/snapshots --snapshot-update    # after an intended template change
mypy sigmoid_cdk tests
ruff check . && ruff format --check .
```

See what the package does, step by step: `python examples/show_output.py`
(or `python examples/show_output.py examples/multi/config.yaml`).

## Build a package for others

```bash
python -m build            # dist/sigmoid_cdk-0.3.0-py3-none-any.whl
git tag v0.3.0 && git push origin v0.3.0    # the Release workflow attaches the wheel
```

## Extending

- New config field: add it to `sigmoid_cdk/configs/models.py` (and a cross-check if it refers to
  another resource), then use it in a construct.
- New construct: add a class in `sigmoid_cdk/constructs/`, export it in `__init__.py`, wire it into
  `ServerlessWebAppStack`.
- New standard tag: add it to the `tags` dict in `ServerlessWebAppStack`.
- Another rule pack: register it next to `AwsSolutionsChecks` in `aspects/compliance.py`.

## Layout

```
sigmoid_cdk/
  configs/      Pydantic schemas, cross-checks and YAML loader
  constructs/   SecureBucket, SecureTopic, LogKey, SecureLambda, ApiGatewayProxy,
                ServerlessBackend, LambdaTriggers, WebDistribution
  aspects/      TaggingAspect, cdk-nag registration
  stacks/       ServerlessWebAppStack
tests/          unit tests and snapshot tests
examples/       web app, worker and multi examples, walkthrough script
scripts/        verify.py (all quality gates in one command)
```

## Known limitations

- No API authorizer or WAF by default.
- S3 and CloudFront access logging are not enabled yet.
- CORS defaults to all origins; set `cors_allowed_origins` for production.
- The API Gateway request validator cannot validate bodies of proxy routes.
- One stack holds at most 500 CloudFormation resources; every Lambda adds about 5 to 6 and every
  API route a few more. Split very large setups into several stacks.
- Routes are path prefixes (that path and everything below it); per-HTTP-method routing is not
  included. Every route allows all methods.
- SNS uses the AWS-managed key, so AWS services that publish to the topic (for example S3 event
  notifications) need a customer-managed key instead.
- Staging log retention (30 days) is an assumption; the original spec defines only dev and prod.
- SQS triggers are not included yet.
