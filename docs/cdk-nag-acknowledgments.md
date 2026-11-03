# cdk-nag acknowledgements

Each rule below is suppressed on purpose in `aspects/compliance_aspect.py`. Remove a row only together with the code.

| Rule | Why acknowledged | Plan |
|---|---|---|
| AwsSolutions-IAM4 (API Gateway push-to-CloudWatch policy only) | AWS-managed policy is the supported way for the account logging role | Keep |
| AwsSolutions-IAM5 | Wildcards only inside specific ARNs; IAM guardrail blocks bare `*` | Keep |
| AwsSolutions-S1 | No central S3 access-log bucket yet | Add log bucket |
| AwsSolutions-CFR1 | Geo restriction not required | Revisit per app |
| AwsSolutions-CFR2, APIG3 | No WAF yet | Add WAF |
| AwsSolutions-CFR3 | No CloudFront log bucket yet | Add log bucket |
| AwsSolutions-CFR4 | Default certificate until a custom domain exists | Add domain + TLS 1.2 policy |
| AwsSolutions-APIG4, COG4 | No authorizer yet; application checks identity | Add authorizer |

Note: with `auto_delete_objects=True` (dev only) CDK adds its own helper Lambda, which cdk-nag may flag; avoid it or acknowledge it in that app.
