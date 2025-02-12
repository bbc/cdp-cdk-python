import aws_cdk as core
from aws_cdk import (
    # Duration,
    Stack,
    aws_secretsmanager as secretsmanager
)
from constructs import Construct
from ..loaders.cfn_param_loader import ParameterLoader
import os
class SecretsManagerStack(Stack):

    def __init__(self, scope: Construct, id: str, env_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # 🔹 Create a secret in Secrets Manager
        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/'+env_name+'/cdp-serverless.json')
        secret_name = parameter_loader.get_parameter("SecretName")
        self.secret = secretsmanager.Secret(self, secret_name,
            secret_name=secret_name,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key="password",
                exclude_punctuation=True
            )
        )

        # 🔹 Output the Secret ARN (to be used in another stack)
        core.CfnOutput(self, "SecretARN",
            value=self.secret.secret_arn,
            description="The ARN of the stored secret",
            export_name="RedshiftAdminSecretARN"  # ✅ Allows import in another stack
        )