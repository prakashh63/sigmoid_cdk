from aws_cdk.assertions import Match, Template


def test_one_distribution_with_oac(dev_template: Template) -> None:
    dev_template.resource_count_is("AWS::CloudFront::Distribution", 1)
    dev_template.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)


def test_default_behavior_redirects_to_https(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": {
                "DefaultCacheBehavior": {"ViewerProtocolPolicy": "redirect-to-https"}
            }
        },
    )


def test_api_behavior_routes_to_api_gateway(dev_template: Template) -> None:
    dev_template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": {
                "CacheBehaviors": [
                    Match.object_like(
                        {
                            "PathPattern": "api/*",
                            "ViewerProtocolPolicy": "redirect-to-https",
                        }
                    )
                ]
            }
        },
    )
