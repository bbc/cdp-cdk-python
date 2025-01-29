from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_redshift as redshift,
    aws_ec2 as ec2,
    aws_redshiftserverless as redshiftserverless
)

import aws_cdk as core
from constructs import Construct
import os 
import json
from aws_cdk.cloudformation_include import CfnInclude
from .cfn_param_loader import ParameterLoader

class RedshiftRolePolicyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "CdpCdkPythonQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # bucket = s3.Bucket(self, "MyFirstBucketTest", versioned=True)

        # Load parameters from a JSON file
        
        dirname = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()
        parameters_file = os.path.join(dirname, './mle-non-pii-redshift-role-param.json') 
        template_file = os.path.join(dirname, "./mle-non-pii-redshift-role-template.json")

        with open(parameters_file, "r") as f:
            parameters = json.load(f).get("parameters", "")
        print('DbUser: %s' % parameters["DbUser"]) 

        # Include the existing CloudFormation template
        template = CfnInclude(
            self,
            "ExistingTemplate",
            template_file=template_file,
            parameters=parameters
        )
        
 

# Access resources defined in the CloudFormation template
        redshiftCrossAccountRole = template.get_resource("RedshiftCrossAccountRole")

        # Create IAM role for Redshift access
        redshift_role = iam.Role(
            self, 
            "test-non-pii-RedshiftRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
        )

        redshift_role.attach_inline_policy(
            iam.Policy(
                self,
                "ExperimentationRedshiftPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "redshift:GetClusterCredentials",
                            "redshift:CreateClusterUser"
                        ],
                        resources=[
                            "arn:aws:redshift:eu-west-1:977228593394:dbuser:test-idl-redshift-component-comp-redshiftcluster/experimentation_airflow",
                            "arn:aws:redshift:eu-west-1:977228593394:dbname:test-idl-redshift-component-comp-redshiftcluster/redshiftdb"
                        ],
                    )
                ],
            )
        )

        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/cdp-pii-datashare.json')
        vpc_id = parameter_loader.get_parameter("VpcId")
        subnet_ids = parameter_loader.get_parameter("SubnetId")
        secret_name = parameter_loader.get_parameter("SecretName")

        # Create Redshift Serverless Namespace
        namespace = redshiftserverless.CfnNamespace(
            self, "RedshiftNamespace",
            namespace_name="my-redshift-namespace",
            admin_username="admin",
            admin_user_password="YourSecurePassword123!",  # Use Secrets Manager for production
            iam_roles=[redshift_role.role_arn]
        )

        redshift_sg = ec2.SecurityGroup(
            self, "RedshiftSG",
            vpc=vpc_id,
            description="Allow Redshift Serverless traffic"
        )

        # 🚪 Allow inbound traffic on Redshift's default port (5439)
        redshift_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),  # Change this to restrict access
            ec2.Port.tcp(5439),
            "Allow Redshift inbound traffic",
            from_port=5439
        )

        redshift_sg.add_egress_rule(
            ec2.Peer.any_ipv4(),  # Change this to restrict access
            ec2.Port.tcp(5439),
            "Allow Redshift inbound traffic",
            from_port=5439
        )

        # Create Redshift Serverless Workgroup
        workgroup = redshiftserverless.CfnWorkgroup(
            self, "RedshiftWorkgroup",
            workgroup_name="my-redshift-workgroup",
            namespace_name=namespace.namespace_name,
            base_capacity=32,  # Base capacity in Redshift Processing Units (RPUs)
            publicly_accessible=False,
            subnet_ids=["subnet-03cbf98aa73d606dd", "subnet-0c2f248e008785559", "subnet-0c30c2b421ce0f84a"],  
            security_group_ids=[redshift_sg.security_group_id]  
        )

        
        
        
    
        core.CfnOutput(
            self, 
            "NamespaceArn", 
            value=namespace.attr_namespace_namespace_arn)
        core.CfnOutput(
            self, 
            "WorkgroupEndpoint", 
            value=workgroup.attr_workgroup_endpoint_address)
        core.CfnOutput(
            self, 
            "RoleArn1", 
            value=f"arn:aws:iam:::{redshiftCrossAccountRole.ref}")
        core.CfnOutput(
            self, 
            "RoleArn2", 
            value=redshift_role.role_arn)
        
