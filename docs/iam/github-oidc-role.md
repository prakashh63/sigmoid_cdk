# GitHub OIDC deploy role

`deploy.yml` signs in to AWS without stored keys. Create this once per AWS account.

1. IAM -> Identity providers -> add `token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. Create a role with this trust policy (replace `ACCOUNT_ID` and `ORG/REPO`):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
      "StringLike": {"token.actions.githubusercontent.com:sub": "repo:ORG/REPO:environment:*"}
    }
  }]
}
```
3. Permissions: allow `sts:AssumeRole` on the CDK bootstrap roles
   (`arn:aws:iam::ACCOUNT_ID:role/cdk-*`). Those roles hold the real deploy permissions.
4. In GitHub: add secret `AWS_DEPLOY_ROLE_ARN`, and create environments `dev`, `staging`, `prod`
   (add required reviewers on `prod`).
