"""CloudFront in front of a private S3 bucket (OAC) and, optionally, an API Gateway at /api/*."""

from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct

from sigmoid_cdk.application_constants import API_PATH_PREFIX
from sigmoid_cdk.application_context import SigmoidContext
from sigmoid_cdk.configs.cloudfront_config import CloudFrontConfig

_PRICE_CLASSES = {
    "100": cloudfront.PriceClass.PRICE_CLASS_100,
    "200": cloudfront.PriceClass.PRICE_CLASS_200,
    "ALL": cloudfront.PriceClass.PRICE_CLASS_ALL,
}


class WebDistribution(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        context: SigmoidContext,
        config: CloudFrontConfig,
        frontend_bucket: s3.IBucket,
        api: apigw.RestApi | None,
    ) -> None:
        super().__init__(scope, construct_id)
        # Origin Access Control: S3 only answers CloudFront, never the public internet.
        bucket_origin = origins.S3BucketOrigin.with_origin_access_control(
            frontend_bucket
        )

        api_behaviors: dict[str, cloudfront.BehaviorOptions] = {}
        if api is not None:
            api_behaviors[f"{API_PATH_PREFIX}/*"] = cloudfront.BehaviorOptions(
                origin=origins.RestApiOrigin(api),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            comment=f"{context.application} ({context.stage})",
            default_root_object=config.default_root_object,
            price_class=_PRICE_CLASSES[config.price_class],
            http_version=cloudfront.HttpVersion.HTTP2_AND_3,
            default_behavior=cloudfront.BehaviorOptions(
                origin=bucket_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            additional_behaviors=api_behaviors,
        )
