# Feature flags

Set in `cdk.json` under `context`, on the command line (`-c key=value`) or in `FeatureFlags(...)`.

| Context key | Default | Effect |
|---|---|---|
| `sigmoid:compliance-checks` | `true` | Runs cdk-nag AwsSolutionsChecks; unacknowledged errors stop synthesis. |
| `sigmoid:iam-guardrails` | `true` | Fails synthesis on `*` actions or `*` resources in IAM policies. |
| `sigmoid:permissions-boundary` | unset | Name of a managed policy attached as permissions boundary to every role. The policy must already exist in the account. |

Turning a flag off must be reviewed in the pull request; CI always runs with the defaults.
