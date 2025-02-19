from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_events as events,
    aws_secretsmanager as secretsmanager,
    aws_events_targets as targets
    
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
        mParticle_api_secret_arn = parameter_loader.get_parameter("mParticleAPISecretARN")
        callback_url = parameter_loader.get_parameter("CallbackUrl")
        sns_topic_arn = parameter_loader.get_parameter("MonitoringTopicArn")
        sns_account_id = parameter_loader.get_parameter("SNSAccountId")

        # Create an IAM Role
        iam_role = iam.Role(
            self, "LambdaCDPAccountRemovalRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Initialize the policy loader
        policy_loader = PolicyLoader(policy_dir="cdp_cdk_python/policies")

        # Load the policy with variable replacements
        lambda_basic_execution_doc = policy_loader.load_policy(
            file_name="lambda_basic_execution.json",
            replacements={}
        )

        cloudwatch_metric_doc = policy_loader.load_policy(
            file_name="cloudwatch_metric.json",
            replacements={}
        )
        
        get_secret_value_doc = policy_loader.load_policy(
            file_name="get_secret_value.json",
            replacements={"SecretArn":mParticle_api_secret_arn}
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
                "CloudwatchMetricPolicy",
                document=cloudwatch_metric_doc
            ),
        )
        
        iam_role.attach_inline_policy(
            iam.Policy(
                self, 
                "GetSecretValuePolicy",
                document=get_secret_value_doc
            )
        )

        dlq = sqs.Queue(
            self, env_name+"-cdp-account-delete-dlq",
            queue_name=env_name+"-cdp-account-delete-dlq",
            retention_period=core.Duration.days(14)  # Messages are kept for 14 days
        )

        # ✅ Create Main SQS Queue with DLQ
        queue = sqs.Queue(
            self, env_name+"-cdp-account-delete",
            queue_name=env_name+"-cdp-account-delete",
            visibility_timeout=core.Duration.seconds(30),  # Message visibility timeout
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=5,  # Move messages to DLQ after 5 failures
                queue=dlq
            )
        )

        queue.node.add_dependency(dlq)

        # ✅ IAM Policy to Allow Sending Messages to SQS
        send_message_policy = iam.PolicyStatement(
            actions=["sqs:SendMessage"],
            effect=iam.Effect.ALLOW,
            resources=[queue.queue_arn],
            principals=[iam.AccountPrincipal(sns_account_id)],  # Allowing all users in the same AWS Account
            conditions={"ArnEquals": {"aws:SourceArn": sns_topic_arn}}
        )

        queue.add_to_resource_policy(send_message_policy)
        
        queue_subscription = sns_subs.SqsSubscription(queue)
        sns_topic = sns.Topic.from_topic_arn(self, "RemoteImportedAccountDeletionSNSTopic", sns_topic_arn)
        queue_subscription.bind(sns_topic)
  

        # ✅ Output Queue ARN
        core.CfnOutput(self, "QueueArn", value=queue.queue_arn)
        core.CfnOutput(self, "DLQArn", value=dlq.queue_arn)

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
            # handler="cdp_delete_account.lambda_handler",
            handler="index.lambda_handler",  # Fake handler reference
            environment={
                "queue_url": queue_url,
                "dead_letter_queue_url": dead_letter_queue_url,
                "external_endpoint_post_url": external_endpoint_post_url,
                "mParticle_api_secret_arn":mParticle_api_secret_arn,
                "callback_url": callback_url
            },
            code=_lambda.InlineCode(
                "def lambda_handler(event, context):\n"
                "    print('Hello from CDK Lambda!')\n"
                "    return {'statusCode': 200, 'body': 'Hello World'}"
            ),
            # code=_lambda.Code.from_asset(
                # "cdp_cdk_python/lambda_function/cdp_delete_account", 
                # bundling={
                #     "image": _lambda.Runtime.PYTHON_3_12.bundling_image,
                #     "command": [
                #         "bash", "-c",
                #         "pip install -r requirements.txt -t /asset-output && cp -r . /asset-output"
                #     ],
                # }
            # ),
            timeout=core.Duration.seconds(30),
            memory_size=memory_param.value_as_number,
            role=iam_role
        )


        rule = events.Rule(
            self, "MyEventRule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="9",
                day="*",      # Every day
                month="*",    # Every month
                year="*",     # Every year
            )
        )

        # ✅ Set the Rule Target as the Lambda Function
        rule.add_target(targets.LambdaFunction(post_deployment_lambda))

        core.CfnOutput(
            self, 
            "RoleArn", 
            value=iam_role.role_arn)
        
        core.CfnOutput(
            self, 
            "FunctionArn", 
            value=post_deployment_lambda.function_arn)
        
        core.CfnOutput(
            self, 
            "ImportedTopicArn", 
            value=sns_topic.topic_arn)
