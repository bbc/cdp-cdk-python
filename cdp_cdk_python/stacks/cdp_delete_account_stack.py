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
import os 
from constructs import Construct
from ..loaders.policy_loader import PolicyLoader
# from .param_loader import ParameterLoader
from ..loaders.cfn_param_loader import ParameterLoader
from ..stacks.secrets_manager_stack import SecretsManagerStack
from aws_cdk.custom_resources import Provider

class CDPDeleteAccountStack(Stack):
    def __init__(self, scope: Construct, id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/'+env_name+'/cdp-delete-account.json')
        queue_url = parameter_loader.get_parameter("QueueUrl")
        dead_letter_queue_url = parameter_loader.get_parameter("DLQUrl")
        external_endpoint_post_url = parameter_loader.get_parameter("ExternalEndpointPostUrl")
        api_key = parameter_loader.get_parameter("MParticleAPIKey")
        api_secret = parameter_loader.get_parameter("MParticleAPISecret")
        callback_url = parameter_loader.get_parameter("CallbackUrl")
        monitoring_topic_arn = parameter_loader.get_parameter("MonitoringTopicArn")

        # Create an IAM Role
        iam_role = iam.Role(
            self, "MyIAMRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Initialize the policy loader
        policy_loader = PolicyLoader(policy_dir="cdp_cdk_python/policies")

        # Load the policy with variable replacements
        lambda_basic_execution_doc = policy_loader.load_policy(
            file_name="lambda_basic_execution.json",
            replacements={}
        )

        

        describe_statement_doc = policy_loader.load_policy(
            file_name="describe_statement.json",
            replacements={}
        )

        
        iam_role.attach_inline_policy(
            iam.Policy(
                self, 
                "LambdaBasicExecutionPolicy",
                document=lambda_basic_execution_doc
            ),
        )
        
        


        iam_role.attach_inline_policy(
            iam.Policy(
                self, 
                "DescribeStatementPolicy",
                document=describe_statement_doc
            )
        )

        
        
        # Define a parameter for Lambda memory size
        memory_param = core.CfnParameter(
            self,
            "MemorySize",
            type="Number",
            description="Memory size for the Lambda function in MB",
            default=128,  # Default memory size
            min_value=128,
            max_value=10240,  # Maximum memory supported by AWS Lambda
        )

        post_deployment_lambda = _lambda.Function(
            self, 
            "MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="cdp_delete_account.lambda_handler",
            environment={
                "queue_url": queue_url,
                "dead_letter_queue_url": dead_letter_queue_url,
                "external_endpoint_post_url": external_endpoint_post_url,
                "api_key": api_key,
                "api_secret": api_secret,
                "callback_url": callback_url,
                "monitoring_topic_arn": monitoring_topic_arn
            },
            code=_lambda.Code.from_asset("cdp_cdk_python/lambda_function/cdp_delete_account"),
            timeout=core.Duration.seconds(30),
            memory_size=memory_param.value_as_number,
            role=iam_role
        )

        core.CfnOutput(
            self, 
            "RoleArn", 
            value=iam_role.role_arn)
        
        core.CfnOutput(
            self, 
            "FunctionArn", 
            value=post_deployment_lambda.function_arn)
