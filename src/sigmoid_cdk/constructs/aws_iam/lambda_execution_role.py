"""Least-privilege execution role: one role per function, logs to its own log group only."""

from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.helpers.name_helper import physical_name
from sigmoid_cdk.utilities.iam_actions import LOG_WRITE_ACTIONS


class LambdaExecutionRole(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        function_name: str,
        log_group: logs.ILogGroup,
    ) -> None:
        super().__init__(scope, construct_id)
        self.role = iam.Role(
            self,
            "Role",
            role_name=physical_name(context, function_name, "role"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=f"Execution role of Lambda function {function_name}",
        )
        # No AWS-managed policy is attached: the role may only write to its own log group.
        self.role.add_to_policy(
            iam.PolicyStatement(
                sid="WriteOwnLogsOnly",
                actions=list(LOG_WRITE_ACTIONS),
                resources=[log_group.log_group_arn],
            )
        )
