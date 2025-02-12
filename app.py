#!/usr/bin/env python3
import os

# import sys
# sys.path += ['/usr/local/lib/python3.12/site-packages','/var/lib/jenkins/.local/lib/python3.12/site-packages']
import aws_cdk as core

from cdp_cdk_python.stacks.cdp_pii_datashare_stack import CdpPiiDatashareStack
from cdp_cdk_python.stacks.redshift_role_policy_stack import RedshiftRolePolicyStack
from cdp_cdk_python.stacks.secrets_manager_stack import SecretsManagerStack
from cdp_cdk_python.stacks.scv_consumer_datashare_stack import ScvConsumerDatashareStack
from cdp_cdk_python.stacks.cdp_delete_account_stack import CDPDeleteAccountStack

app = core.App()
env_name = app.node.try_get_context("env")
# os.environ["CDK_DEFAULT_ACCOUNT"] = "977228593394"
secrets_stack = SecretsManagerStack(app, "SecretsManagerStack", env_name=env_name, 
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )
CdpPiiDatashareStack(app, "CdpPiiDatashareStack", env_name=env_name,  
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )
ScvConsumerDatashareStack(app, "ScvConsumerDatashareStack", env_name=env_name,  
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )
# RedshiftRolePolicyStack(app, "RedshiftRolePolicyStack", secrets_stack=secrets_stack, env_name=env_name, 
#                       env=core.Environment(
#                         account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
#                         region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
#                       )
#                     )
CDPDeleteAccountStack(app, "CDPDeleteAccountStack", env_name=env_name, 
                      env=core.Environment(
                        account=os.getenv("CDK_DEFAULT_ACCOUNT"),  # Uses the default AWS account
                        region=os.getenv("CDK_DEFAULT_REGION")  # Uses the default AWS region
                      )
                    )
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    

app.synth()
