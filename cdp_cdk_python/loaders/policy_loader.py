import json
from aws_cdk import aws_iam as iam
import re
import aws_cdk as core

class PolicyLoader:
    def __init__(self, policy_dir: str):
        """
        Initialize the IAMPolicyLoader with the directory containing policy files.
        :param policy_dir: Directory where JSON policy files are stored.
        """
        self.policy_dir = policy_dir

    def load_policy(self, file_name: str, replacements: dict) -> iam.PolicyDocument:
        policy_json = self._do_replace(file_name, replacements) 
        print(str(policy_json))
        # policy_data = policy_json
        # statements = []
        # for statement in policy_data["Statement"]:
        #     print("Resource", statement["Resource"])
        #     resource = core.Fn.sub(statement["Resource"], replacements)
        #     policy_statement = iam.PolicyStatement(
        #         effect=iam.Effect.ALLOW if statement["Effect"] == "Allow" else iam.Effect.DENY,
        #         actions=[statement["Action"]] if isinstance(statement["Action"], str) else statement["Action"],
        #         resources=[resource] if isinstance(resource, str) else resource
        #     )
        #     statements.append(policy_statement)
        try:
            # policy_doc = iam.PolicyDocument(statements=statements)
            policy_doc = iam.PolicyDocument.from_json(policy_json)
        except Exception as e:
            print(f"An error occurred: {str(e)}") 
        return policy_doc

    def _do_replace(self, file_name: str, replacements: dict) -> str:
        """
        Load an IAM policy file and replace placeholders with provided variables.
        :param file_name: Name of the policy JSON file.
        :param variables: Dictionary of variable replacements.
        :return: An IAM PolicyDocument object.
        """
        self.replacements = replacements
        file_path = f"{self.policy_dir}/{file_name}"
        with open(file_path, "r") as f:
            policy_json = json.load(f)
        print(policy_json)
        policy_json = self._replace_refs(policy_json)
        print(policy_json)
        policy_json = self._replace_placeholders(policy_json)
        print(policy_json)
        return policy_json
        
    
    def _replace_refs(self, obj):
        """
        Recursively replace "Ref" keys with values from the replacements dictionary.

        :param obj: The policy object (dict, list, or value).
        :return: The object with "Ref" values replaced.
        """
        if isinstance(obj, dict):
            if "Ref" in obj:
                ref_value = obj["Ref"]
                if ref_value in self.replacements:
                    return self.replacements[ref_value]
                else:
                    raise KeyError(f"Reference '{ref_value}' not found in replacements.")
            elif "Fn::Sub" in obj:
                template_string = obj["Fn::Sub"]
                variable_names = re.findall(r"\${([A-Za-z0-9_]+)}", template_string)
                missing_vars = [var for var in variable_names if var not in self.replacements]
                if not missing_vars:
                    return core.Fn.sub(template_string, self.replacements)
                else:
                    raise KeyError(f"missing vars '{missing_vars}' not found in replacements.")
            else:
                return {k: self._replace_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_refs(item) for item in obj]
        else:
            return obj

    def _replace_placeholders(self, obj):
        """
        Recursively replace "${..}" placeholders with values from the replacements dictionary.

        :param obj: The policy object (dict, list, or value).
        :return: The object with placeholders replaced.
        """
        if isinstance(obj, str):
            # Replace placeholders like "${Key}" with their values
            obj = re.sub(
                r"\$\{([^}]+)\}",
                lambda match: self.replacements.get(match.group(1), match.group(0)),
                obj,
            )
            print('obj:',obj)
            return obj
            # return regexSub.replace('','')
            # return core.Fn.sub(obj, self.replacements)
        elif isinstance(obj, dict):
            return {k: self._replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_placeholders(item) for item in obj]
        else:
            return obj
        

        # # Replace placeholders in the policy
        # policy_str = json.dumps(policy_json)
        # for key, value in variables.items():
        #     placeholder = f"${{{key}}}"  # e.g., ${bucket_name}
        #     policy_str = policy_str.replace(placeholder, value)
        #     print(placeholder)
        #     print(value)
        # # Convert the processed policy back to JSON and create a PolicyDocument
        # processed_policy = json.loads(policy_str)
        # try:
        #     policy_doc = iam.PolicyDocument.from_json(processed_policy)
        # except Exception as e:
        #     print(f"An error occurred: {str(e)}") 
        # return policy_doc

    