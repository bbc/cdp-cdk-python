import aws_cdk as core
import aws_cdk.aws_secretsmanager as secretsmanager

class SecretsManagerStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
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