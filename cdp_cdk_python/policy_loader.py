import json
from aws_cdk import aws_iam as iam
import re

class PolicyLoader:
    def __init__(self, policy_dir: str):
        """
        Initialize the IAMPolicyLoader with the directory containing policy files.
        :param policy_dir: Directory where JSON policy files are stored.
        """
        self.policy_dir = policy_dir

    def load_policy(self, file_name: str, replacements: dict) -> iam.PolicyDocument:
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
        policy_json = self._replace_refs(policy_json)
        policy_json = self._replace_placeholders(policy_json)
        policy_doc = iam.PolicyDocument.from_json(policy_json)
        return policy_doc
    
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
            return re.sub(
                r"\$\{([^}]+)\}",
                lambda match: self.replacements.get(match.group(1), match.group(0)),
                obj,
            )
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

    