"""API Gateway REST API with throttling, CORS, request validation and encrypted access logs."""

from collections.abc import Mapping

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.api_gateway_config import ApiGatewayConfig
from sigmoid_cdk.constructs.aws_logs.secure_log_group import SecureLogGroup
from sigmoid_cdk.helpers.name_helper import physical_name

_ACCOUNT_LOGGING_ID = "ApiGatewayAccountLogging"


class ApiGatewayAccountLogging(Construct):
    """The account-wide role API Gateway needs to write logs. Created once per stack."""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonAPIGatewayPushToCloudWatchLogs"
                )
            ],
        )
        self.account = apigw.CfnAccount(
            self, "Account", cloud_watch_role_arn=role.role_arn
        )

    @classmethod
    def get_or_create(cls, stack: cdk.Stack) -> "ApiGatewayAccountLogging":
        existing = stack.node.try_find_child(_ACCOUNT_LOGGING_ID)
        if isinstance(existing, ApiGatewayAccountLogging):
            return existing
        return cls(stack, _ACCOUNT_LOGGING_ID)


class SigmoidRestApi(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: ApiGatewayConfig,
        log_key: kms.IKey,
        functions: Mapping[str, lambda_.IFunction],
    ) -> None:
        super().__init__(scope, construct_id)
        api_name = physical_name(context, config.api_name)
        access_logs = SecureLogGroup(
            self,
            "AccessLogGroup",
            context=context,
            log_group_name=f"/aws/apigateway/{api_name}-access",
            encryption_key=log_key,
        )
        cors = (
            apigw.CorsOptions(
                allow_origins=config.cors_allowed_origins,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            )
            if config.enable_cors
            else None
        )
        self.rest_api = apigw.RestApi(
            self,
            "RestApi",
            rest_api_name=api_name,
            cloud_watch_role=False,  # one shared account role is created instead
            endpoint_types=[apigw.EndpointType.REGIONAL],
            default_cors_preflight_options=cors,
            deploy_options=apigw.StageOptions(
                stage_name=config.stage_name,
                throttling_rate_limit=config.rate_limit,
                throttling_burst_limit=config.burst_limit,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
                metrics_enabled=True,
                access_log_destination=apigw.LogGroupLogDestination(
                    access_logs.log_group
                ),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(
                    caller=False,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=False,
                ),
            ),
        )
        account_logging = ApiGatewayAccountLogging.get_or_create(cdk.Stack.of(self))
        self.rest_api.node.add_dependency(account_logging)

        validator = self.rest_api.add_request_validator(
            "RequestValidator",
            validate_request_body=True,
            validate_request_parameters=True,
        )
        resources: dict[str, apigw.IResource] = {"": self.rest_api.root}
        for route in config.routes:
            resource = self._resource_for(resources, route.path)
            resource.add_method(
                route.http_method,
                apigw.LambdaIntegration(functions[route.lambda_name], proxy=True),
                request_validator=validator,
            )

    @staticmethod
    def _resource_for(
        resources: dict[str, apigw.IResource], path: str
    ) -> apigw.IResource:
        """Creates every missing path segment, for example api -> orders -> {order_id}."""
        current_path = ""
        current = resources[""]
        for segment in path.split("/"):
            current_path = f"{current_path}/{segment}" if current_path else segment
            if current_path not in resources:
                resources[current_path] = current.add_resource(segment)
            current = resources[current_path]
        return current
