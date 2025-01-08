from aws_cdk import (
    core as cdk,
    aws_iam as iam,
)
from policy_loader import PolicyLoader

class LambdaRolePolicyStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an IAM Role
        iam_role = iam.Role(
            self, "MyIAMRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Initialize the policy loader
        policy_loader = PolicyLoader(policy_dir="policies")

        # Load the policy with variable replacements
        policy1 = policy_loader.load_policy(
            file_name="lambda_basic_execution.json",
            variables={}
        )

        # Attach the policy to the IAM role
        policy_loader.attach_policy_to_role(
            role=iam_role,
            policy_name="S3AccessPolicy",
            policy_document=policy1
        )
