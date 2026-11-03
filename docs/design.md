# Design

```
SigmoidApp -> ServerlessWebAppStack (extends SigmoidStack)
                |- LogEncryptionKey            one KMS key for all log groups
                |- SecureBucket (1..n)         frontend bucket + data buckets
                |- QueueWithDeadLetterQueue    0..n
                |- ServerlessBackend           layers, Lambda functions, REST APIs
                |- SigmoidEventRule            0..n
                '- WebDistribution             CloudFront: S3 (OAC) default, /api/* -> API Gateway
```

* **Configs** (pydantic) validate everything, including cross references, before CDK runs.
* **Constructs** are small L3 wrappers; each one hard-codes its security settings.
* **Aspects** run at synth time: tagging, cdk-nag, IAM guardrails, optional permissions boundary.
* **Stage rules** live in one table (`utilities/stage_policies.py`).

Decisions
* CloudFront forwards `/api/*` unchanged, so every route of the API behind CloudFront starts with `api/`.
* There is no single-page-app 403/404 fallback: CloudFront applies such rules to the API too and would hide API errors.
* One shared account-level API Gateway logging role per stack (several APIs would otherwise conflict).
* Input is Python (pydantic), not YAML.
