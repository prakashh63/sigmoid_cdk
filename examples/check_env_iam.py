"""Show the account, region and IAM that sigmoid_cdk produces. Nothing is deployed.

Usage:  python examples/check_env_iam.py [path/to/config.yaml]
Try:    CDK_DEFAULT_ACCOUNT=123456789012 CDK_DEFAULT_REGION=ap-south-1 \
            python examples/check_env_iam.py
"""

import json
import sys
from pathlib import Path
from typing import Any

import aws_cdk as cdk
from aws_cdk.assertions import Template

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import load_config

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "config.yaml"
stack = ServerlessWebAppStack(cdk.App(), "CheckStack", config=load_config(path), enable_compliance=False)


def show(value: str) -> str:
    return "(open: filled in at deploy time from your login)" if cdk.Token.is_unresolved(value) else value


print("== ACCOUNT AND REGION ==")
print(f"  account : {show(stack.account)}")
print(f"  region  : {show(stack.region)}")

template: dict[str, Any] = Template.from_stack(stack).to_json()
resources: dict[str, Any] = template["Resources"]

print("\n== IAM ROLES (who can act) ==")
for logical_id, res in resources.items():
    if res["Type"] != "AWS::IAM::Role":
        continue
    principal = res["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"]
    managed = res["Properties"].get("ManagedPolicyArns")
    print(f"  {logical_id}")
    print(f"      assumed by : {principal}")
    print(f"      managed policies: {'yes (AWS-managed, see README IAM4)' if managed else 'none'}")

print("\n== IAM POLICIES (what each role may do) ==")
for logical_id, res in resources.items():
    if res["Type"] != "AWS::IAM::Policy":
        continue
    roles = [r.get("Ref") for r in res["Properties"]["Roles"]]
    print(f"  {logical_id[:60]}  -> roles {roles}")
    for statement in res["Properties"]["PolicyDocument"]["Statement"]:
        actions = statement["Action"]
        actions = actions if isinstance(actions, list) else [actions]
        resource = json.dumps(statement["Resource"])[:90]
        print(f"      {statement['Effect']}: {actions}")
        print(f"          on {resource}")
        if "*" in actions or "s3:*" in actions:
            print("          !! wildcard action")

print("\n== RESOURCE POLICIES (who can reach a resource) ==")
for logical_id, res in resources.items():
    if res["Type"] in ("AWS::S3::BucketPolicy", "AWS::SNS::TopicPolicy"):
        print(f"  {res['Type']}: {logical_id[:60]}")
    if res["Type"] == "AWS::KMS::Key":
        sids = [s.get("Sid", "(root admin)") for s in res["Properties"]["KeyPolicy"]["Statement"]]
        print(f"  KMS key policy statements: {sids}")