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
        # lambda_basic_execution = policy_loader.load_policy(
        #     file_name="lambda_basic_execution.json",
        #     variables={}
        # )
        lambda_basic_execution_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"],
                    resources=["*"]
                )
            ]
        )

        # Attach the policy to the IAM role
        print("lambda_basic_execution doc:", lambda_basic_execution_doc)
        inline_policy = iam.Policy(
                self, 
                "LambdaBasicExecutionPolicy",
                document=lambda_basic_execution_doc
        )
        iam_role.attach_inline_policy(inline_policy)
        # print("lambda_basic_execution string:", lambda_basic_execution.to_json.__str__)
        # policy_loader.attach_policy_to_role(
        #     role=iam_role,
        #     policy_name="LambdaBasicExecutionPolicy",
        #     policy_document=lambda_basic_execution_doc
        # )

        core.CfnOutput(
            self, 
            "RoleArn", 
            value=iam_role.role_arn)
        # core.CfnOutput(
        #     self, 
        #     "FunctionArn", 
        #     value=lambda_basic_execution.to_json.__str__)
