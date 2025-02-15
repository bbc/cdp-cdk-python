from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_redshift as redshift,
    aws_ec2 as ec2,
    aws_redshiftserverless as redshiftserverless,
    aws_secretsmanager as secretsmanager
)

import aws_cdk as core
from constructs import Construct
import os 
import json
from aws_cdk.cloudformation_include import CfnInclude
from ..loaders.cfn_param_loader import ParameterLoader

from cdp_cdk_python.stacks.secrets_manager_stack import SecretsManagerStack

class RedshiftRolePolicyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_name: str, secrets_stack: SecretsManagerStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        parameter_loader = ParameterLoader(self, 'cdp_cdk_python/params/'+env_name+'/cdp-serverless.json')
        vpc_id = parameter_loader.get_parameter("VpcId")
        namespace_name = parameter_loader.get_parameter("NamespaceName")
        workgroup_name = parameter_loader.get_parameter("WorkgroupName")
        db_name = parameter_loader.get_parameter("DatabaseName")
        base_capacity = core.CfnParameter(self, "BaseRPU", type="Number", default=parameter_loader.get_parameter("BaseRPU"))
        publicly_accessible = parameter_loader.get_parameter("PubliclyAccessible")
        is_publicly_accessible = publicly_accessible.lower() == "true"
        enhanced_vpc_routing = parameter_loader.get_parameter("EnhancedVpcRouting")
        is_enhanced_vpc_routing = enhanced_vpc_routing.lower() == "true"
        subnet_ids = core.CfnParameter(self, "SubnetId", type="CommaDelimitedList", default=parameter_loader.get_parameter("SubnetId"))
        print("subnet_ids:",subnet_ids)
        
        secret_arn = secrets_stack.secret.secret_arn
        print(secret_arn)
        secret = secretsmanager.Secret.from_secret_complete_arn(self, "ImportedSecret", secret_arn)
        admin_password = secret.secret_value_from_json("password").unsafe_unwrap()
        print(admin_password)
        core.CfnOutput(self, "RetrievedSecretARN",
            value=secret.secret_arn,
            description="The ARN of the imported secret"
        )

        # Create Redshift Serverless Namespace
        namespace = redshiftserverless.CfnNamespace(
            self, "RedshiftNamespace",
            namespace_name=namespace_name,
            admin_username="admin",
            admin_user_password=admin_password,
            db_name=db_name,
            iam_roles=[redshift_role.role_arn]
        )

        redshift_sg = ec2.CfnSecurityGroup(self, "MyCfnSecurityGroup",
            group_description="Allow Redshift",
            vpc_id=vpc_id,
            security_group_ingress=[{
                "ipProtocol": "tcp",
                "fromPort": 5439,
                "toPort": 5439,
                "cidrIp": "0.0.0.0/0"
            }],
            security_group_egress=[{
                "ipProtocol": "tcp",
                "fromPort": 5439,
                "toPort": 5439,
                "cidrIp": "0.0.0.0/0"
            }]
        )
        


        # Create Redshift Serverless Workgroup
        workgroup = redshiftserverless.CfnWorkgroup(
            self, "RedshiftWorkgroup",
            workgroup_name=workgroup_name,
            namespace_name=namespace_name,
            base_capacity=base_capacity.value_as_number,  # Base capacity in Redshift Processing Units (RPUs)
            publicly_accessible=is_publicly_accessible,
            enhanced_vpc_routing=is_enhanced_vpc_routing,
            subnet_ids=subnet_ids.value_as_list, #["subnet-03cbf98aa73d606dd", "subnet-0c2f248e008785559", "subnet-0c30c2b421ce0f84a"],  
            security_group_ids=[redshift_sg.attr_group_id]  
        )

        workgroup.add_dependency(namespace)
        workgroup.add_dependency(redshift_sg)
        
    
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
        
