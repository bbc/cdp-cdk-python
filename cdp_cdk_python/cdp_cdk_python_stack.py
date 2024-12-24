from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_iam as iam,
    # aws_redshiftserverless as redshiftserverless,
    
)
import aws_cdk as core
from constructs import Construct

class CdpCdkPythonStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "CdpCdkPythonQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # bucket = s3.Bucket(self, "MyFirstBucketTest", versioned=True)

        # Create IAM role for Redshift access
        redshift_role = iam.Role(
            self, "test-non-pii-RedshiftRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
            ]
        )

        # # Create Redshift Serverless Namespace
        # namespace = redshiftserverless.CfnNamespace(
        #     self, "RedshiftNamespace",
        #     namespace_name="my-redshift-namespace",
        #     admin_username="admin",
        #     admin_user_password="YourSecurePassword123!",  # Use Secrets Manager for production
        #     iam_roles=[redshift_role.role_arn]
        # )

        # # Create Redshift Serverless Workgroup
        # workgroup = redshiftserverless.CfnWorkgroup(
        #     self, "RedshiftWorkgroup",
        #     workgroup_name="my-redshift-workgroup",
        #     namespace_name=namespace.namespace_name,
        #     base_capacity=32,  # Base capacity in Redshift Processing Units (RPUs)
        #     publicly_accessible=True,
        #     subnet_ids=["subnet-xxxxxxx", "subnet-yyyyyyy"],  # Replace with actual subnet IDs
        #     security_group_ids=["sg-zzzzzzzz"]  # Replace with actual security group IDs
        # )

        # core.CfnOutput(self, "WorkgroupEndpoint", value=workgroup.attr_endpoint_address)
