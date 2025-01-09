from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    # aws_redshiftserverless as redshiftserverless,
    
)
import aws_cdk as core
from constructs import Construct
from .policy_loader import PolicyLoader

class LambdaRolePolicyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an IAM Role
        iam_role = iam.Role(
            self, "MyIAMRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Initialize the policy loader
        policy_loader = PolicyLoader(policy_dir="cdp_cdk_python/policies")

        # Load the policy with variable replacements
        lambda_basic_execution = policy_loader.load_policy(
            file_name="lambda_basic_execution.json",
            variables={}
        )

        # Attach the policy to the IAM role
        print("lambda_basic_execution:", lambda_basic_execution)
        print("lambda_basic_execution string:", lambda_basic_execution.to_json.__str__)
        policy_loader.attach_policy_to_role(
            role=iam_role,
            policy_name="LambdaBasicExecutionPolicy",
            policy_document=lambda_basic_execution
        )

        core.CfnOutput(
            self, 
            "RoleArn", 
            value=iam_role.role_arn)
        core.CfnOutput(
            self, 
            "FunctionArn", 
            value=lambda_basic_execution)
