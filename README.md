# sigmoid-cdk

An internal Python package that turns a short configuration into a complete, secure serverless web
application on AWS: **S3 + CloudFront (OAC) + API Gateway + Lambda**, plus **SQS** and **EventBridge**.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
npm install -g aws-cdk        # the CDK command line
```

## Use it (examples/app.py, under 30 lines)

```python
from sigmoid_cdk import SigmoidApp
from sigmoid_cdk.configs import ApiGatewayConfig, AppSettings, LambdaConfig, S3Config

app = SigmoidApp(
    AppSettings(
        app_name="customer-portal",
        environment="prod",
        owner_team="frontend-devs",
        s3=S3Config(bucket_name="cust-portal-web-assets-prod"),
        lambda_backend=LambdaConfig(
            function_name="portal-api-handler", entry_point_dir="examples/lambda_src"
        ),
        api_gateway=ApiGatewayConfig(stage_name="v1", rate_limit=2000),
    )
)
app.synth()
```

Bigger applications (several Lambdas, APIs, queues, schedules) use `WebAppConfig`; see
`docs/getting-started.md`.

## Commands

| Task | Command |
|---|---|
| Tests | `pytest` |
| Update snapshots | `pytest tests/snapshots --snapshot-update` |
| Types | `mypy` |
| Style | `ruff check . && ruff format --check .` |
| Conventions | `python tools/check_conventions.py` |
| Synthesize | `cdk synth` |
| IAM report | `python tools/iam_report.py cdk.out` |

## CI/CD (GitHub Actions)

* `ci.yml` - every push and pull request: ruff, mypy, conventions, pytest (incl. cdk-nag and snapshots), `cdk synth`.
* `release.yml` - on a `v*` tag: builds the wheel and attaches it to a GitHub release.
* `deploy.yml` - manual: pick the stage, shows `cdk diff`, then deploys through a GitHub OIDC role
  (see `docs/iam/github-oidc-role.md`). Needs the repository secret `AWS_DEPLOY_ROLE_ARN`.

## Documentation

`docs/` holds the design, naming rules, feature flags, locked/adjustable security defaults,
cdk-nag acknowledgements and the IAM documents.
