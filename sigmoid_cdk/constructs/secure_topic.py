"""SecureTopic: an SNS topic (encrypted, SSL only) that several Lambdas can subscribe to."""

from aws_cdk import aws_kms as kms
from aws_cdk import aws_sns as sns
from constructs import Construct


class SecureTopic(Construct):
    """Encrypted with the AWS-managed SNS key (no extra key cost); publishing needs SSL."""

    def __init__(self, scope: Construct, construct_id: str, *, topic_name: str) -> None:
        super().__init__(scope, construct_id)

        sns_key: kms.IKey = kms.Alias.from_alias_name(self, "SnsKey", "alias/aws/sns")
        self.topic = sns.Topic(
            self,
            "Topic",
            topic_name=topic_name,
            enforce_ssl=True,
            master_key=sns_key,
        )
