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

class LambdaRolePolicyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Load parameters from the JSON file
        # parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/cdp-pii-datashare.json')
        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/cdp-pii-datashare.json')
        cluster_name = parameter_loader.get_parameter("ClusterName")
        secret_arn = parameter_loader.get_parameter("SecretArn")
        
        print(cluster_name)
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
            file_name="execute_batch_statement.json",
            replacements={"ClusterName":cluster_name, "AWS::Region":self.region, "AWS::AccountId":self.account}
        )
        # execute_batch_statement_doc = iam.PolicyDocument.from_json(
        #     {
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "redshift-data:BatchExecuteStatement",
        #                     "redshift-data:ExecuteStatement"
        #                 ],
        #                 "Resource": {
        #                     "Fn::Sub": "arn:aws:redshift:${AWS::Region}:${AWS::AccountId}:cluster:${ClusterName}"
        #                 }
        #             }
        #         ]
        #     }

        # )
        

    
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

        fn = _lambda.Function(
            self, 
            "MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            # environment={
                # "CodeVersionString": 1.0,
                # "REGION": core.Stack.region,
                # "AVAILABILITY_ZONES": json.dumps(core.Stack.availability_zones),
            # },
            code=_lambda.Code.from_asset("cdp_cdk_python/lambda_function"),
            timeout=core.Duration.minutes(15),
            memory_size=memory_param.value_as_number,
            role=iam_role
        )

        core.CfnOutput(
            self, 
            "FunctionArn", 
            value=fn.function_arn)
