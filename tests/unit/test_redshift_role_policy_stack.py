import os

import aws_cdk as core
import aws_cdk.assertions as assertions

from cdp_cdk_python.stacks.redshift_role_policy_stack import RedshiftRolePolicyStack
from cdp_cdk_python.stacks.secrets_manager_stack import SecretsManagerStack

def test_redshift_resources_created():
    app = core.App()
    secrets_stack = SecretsManagerStack(app, "SecretsManagerStack", 
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )
    stack = RedshiftRolePolicyStack(app, "RedshiftRolePolicyStack", secrets_stack=secrets_stack,
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )

    template = assertions.Template.from_stack(stack)

    # template.has_resource("AWS::RedshiftServerless::Namespace")

    template.has_resource_properties("AWS::RedshiftServerless::Workgroup", {
        "BaseCapacity": 128,
        "PubliclyAccessible": False
    })
