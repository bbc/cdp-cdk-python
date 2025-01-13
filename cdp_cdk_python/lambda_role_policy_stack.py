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
from .cfn_param_loader import CfnParameterLoader

class LambdaRolePolicyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Load parameters from the JSON file
        parameter_loader = CfnParameterLoader(self, 'cdp_cdk_python/params/cdp-pii-datashare.json')
        cluster_name = parameter_loader.get_parameter("ClusterName")
        secret_arn = parameter_loader.get_parameter("SecretArn")
        print(core.Token.as_string(cluster_name.value_as_string))
        print(core.Token.as_string(secret_arn.value_as_string))

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
            replacements={"SecretArn":secret_arn.value_as_string}#"arn:aws:secretsmanager:eu-west-1:977228593394:secret:redshift-int-scv-redshift-pii-redshiftcluster-11epfp2gjslrr-scvpiiadmin-VeQ6oT"
        )

        accout_id = os.getenv('CDK_DEFAULT_ACCOUNT')
        region = os.getenv('CDK_DEFAULT_REGION')
        execute_batch_statement_doc = policy_loader.load_policy(
            file_name="execute_batch_statement.json",
            replacements={"ClusterName":cluster_name.value_as_string, "AWS::Region":region, "AWS::AccountId":accout_id}
        )
        

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),
        
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
        # core.CfnOutput(
        #     self, 
        #     "FunctionArn", 
        #     value=lambda_basic_execution_doc.to_json.__str__)
