from aws_cdk.assertions import Template

from sigmoid_cdk.helpers.iam_policy_helper import (
    find_policy_violations,
    find_trust_violations,
)


def test_no_policy_breaks_guardrails(full_template: Template) -> None:
    for kind in ("AWS::IAM::Policy", "AWS::IAM::ManagedPolicy"):
        for resource in full_template.find_resources(kind).values():
            assert (
                find_policy_violations(resource["Properties"]["PolicyDocument"]) == []
            )


def test_no_role_is_assumable_by_anyone(full_template: Template) -> None:
    for resource in full_template.find_resources("AWS::IAM::Role").values():
        assert (
            find_trust_violations(resource["Properties"]["AssumeRolePolicyDocument"])
            == []
        )


def test_lambda_roles_trust_only_lambda(full_template: Template) -> None:
    lambda_roles = [
        r
        for r in full_template.find_resources("AWS::IAM::Role").values()
        if r["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"][
            "Service"
        ]
        == "lambda.amazonaws.com"
    ]
    assert len(lambda_roles) == 2
    assert all("ManagedPolicyArns" not in r["Properties"] for r in lambda_roles)
