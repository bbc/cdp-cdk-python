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
from .policy_loader import PolicyLoader
# from .param_loader import ParameterLoader
from .cfn_param_loader import ParameterLoader
from aws_cdk.custom_resources import Provider

class ScvConsumerDatashareStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Load parameters from the JSON file
        # parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/cdp-pii-datashare.json')
        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/scv-consumer-datashare.json')
        datashare_name = parameter_loader.get_parameter("DatashareName")
        workgroup_name = parameter_loader.get_parameter("WorkgroupName")
        database_name_connection = parameter_loader.get_parameter("DatabaseNameConnection")
        database_name_from_datashare = parameter_loader.get_parameter("DatabaseNameFromDatashare")
        secret_arn = parameter_loader.get_parameter("SecretArn")
        producer_account = parameter_loader.get_parameter("ProducerAccount")
        producer_namespace_identifier = parameter_loader.get_parameter("ProducerNamespaceIdentifier")
        
        print(datashare_name)
        print(secret_arn)

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

        get_secret_value_doc = policy_loader.load_policy(
            file_name="get_secret_value.json",
            replacements={"SecretArn":secret_arn}#"arn:aws:secretsmanager:eu-west-1:977228593394:secret:redshift-int-scv-redshift-pii-redshiftcluster-11epfp2gjslrr-scvpiiadmin-VeQ6oT"
        )

        execute_batch_statement_doc = policy_loader.load_policy(
            file_name="execute_batch_statement_workgroup.json",
            replacements={"WorkgroupArn":secret_arn}
        )
        
        # resource_arn = core.Fn.sub("arn:aws:redshift:${AWS::Region}:${AWS::AccountId}:cluster:${ClusterName}", {"Region": self.region, "AccountId": self.account, "ClusterName": cluster_name})
        # print("resource_arn:",resource_arn)
        # execute_batch_statement_doc = iam.PolicyDocument.from_json({
        #     "Statement": [
        #         {
        #             "Effect": "Allow",
        #             "Action": [
        #                 "redshift-data:BatchExecuteStatement",
        #                 "redshift-data:ExecuteStatement"
        #             ],
        #             "Resource": resource_arn  
        #         }
        #     ]
        # })
        

    
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
                "GetSecretValuePolicy",
                document=get_secret_value_doc
            )
        )

        iam_role.attach_inline_policy(
            iam.Policy(
                self, 
                "ExecuteBatchStatementPolicy",
                document=execute_batch_statement_doc
            )
        )

        iam_role.attach_inline_policy(
            iam.Policy(
                self, 
                "DescribeStatementPolicy",
                document=describe_statement_doc
            )
        )

        core.CfnOutput(
            self, 
            "RoleArn", 
            value=iam_role.role_arn)
        
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
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="consumer_datashare.lambda_handler",
            environment={
                "DATASHARE_NAME": datashare_name,
                "WORKGROUP_NAME": workgroup_name,
                "DATABASE_NAME_CONNECTION": database_name_connection,
                "DATABASE_NAME_FROM_DATASHARE": database_name_from_datashare,
                "SECRET_ARN": secret_arn,
                "PRODUCER_ACCOUNT": producer_account,
                "PRODUCER_NAMESPACE_IDENTIFIER": producer_namespace_identifier
            },
            code=_lambda.Code.from_asset("cdp_cdk_python/lambda_function"),
            timeout=core.Duration.seconds(30),
            memory_size=memory_param.value_as_number,
            role=iam_role
        )

        # Custom Resource Provider
        provider = Provider(
            self, "CustomResourceProvider",
            on_event_handler=post_deployment_lambda
        )

        # Custom Resource
        core.CustomResource(
            self, "PostDeploymentAction",
            service_token=provider.service_token,
            properties={
                "Action": "ExecuteAfterDeployment",
                "Parameters": {
                    
                }
            }
        )

        core.CfnOutput(
            self, 
            "FunctionArn", 
            value=post_deployment_lambda.function_arn)
