import aws_cdk as core
from aws_cdk import (
    # Duration,
    Stack,
    aws_secretsmanager as secretsmanager
)
from constructs import Construct

class SecretsManagerStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 🔹 Create a secret in Secrets Manager
        secret = secretsmanager.Secret(self, "MySecret",
            secret_name="CDPRedshiftServerlessSecretsName",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key="password",
                exclude_punctuation=True
            )
        )

        # 🔹 Output the Secret ARN (to be used in another stack)
        core.CfnOutput(self, "SecretARN",
            value=secret.secret_arn,
            description="The ARN of the stored secret",
            export_name="CDPRedshiftServerlessSecretsNameARN"  # ✅ Allows import in another stack
        )