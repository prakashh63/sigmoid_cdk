"""WebDistribution: CloudFront in front of private S3 buckets (OAC) and an optional API."""

from aws_cdk import Acknowledgment, Validations
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct


class WebDistribution(Construct):
    """Default route -> default bucket. Extra paths -> other buckets. /api/* -> API. HTTPS only."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        default_bucket: s3.IBucket,
        path_buckets: dict[str, s3.IBucket] | None = None,
        api: apigw.RestApi | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        redirect = cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS

        additional_behaviors: dict[str, cloudfront.BehaviorOptions] = {}
        if api is not None:
            additional_behaviors["/api/*"] = cloudfront.BehaviorOptions(
                origin=origins.RestApiOrigin(api),
                viewer_protocol_policy=redirect,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
            )
        # Note: CloudFront forwards the full path, so '/assets/x.png' reads the key 'assets/x.png'.
        for pattern, bucket in (path_buckets or {}).items():
            additional_behaviors[pattern] = cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=redirect,
            )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(default_bucket),
                viewer_protocol_policy=redirect,
            ),
            additional_behaviors=additional_behaviors or None,
        )

        Validations.of(self.distribution).acknowledge(
            Acknowledgment(
                id="AwsSolutions::AwsSolutions-CFR1",
                reason="Geo restriction is a per-application business decision.",
            ),
            Acknowledgment(
                id="AwsSolutions::AwsSolutions-CFR2",
                reason="WAF is a paid add-on; enable per application when required.",
            ),
            Acknowledgment(
                id="AwsSolutions::AwsSolutions-CFR3",
                reason="Access logging needs a dedicated log bucket; tracked improvement.",
            ),
            Acknowledgment(
                id="AwsSolutions::AwsSolutions-CFR4",
                reason=(
                    "Default CloudFront certificate; a TLS floor needs a custom domain "
                    "and an ACM certificate."
                ),
            ),
        )
