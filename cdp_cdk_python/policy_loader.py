import json
from aws_cdk import aws_iam as iam

class PolicyLoader:
    def __init__(self, policy_dir: str):
        """
        Initialize the IAMPolicyLoader with the directory containing policy files.
        :param policy_dir: Directory where JSON policy files are stored.
        """
        self.policy_dir = policy_dir

    def load_policy(self, file_name: str, variables: dict) -> iam.PolicyDocument:
        """
        Load an IAM policy file and replace placeholders with provided variables.
        :param file_name: Name of the policy JSON file.
        :param variables: Dictionary of variable replacements.
        :return: An IAM PolicyDocument object.
        """
        file_path = f"{self.policy_dir}/{file_name}"
        with open(file_path, "r") as f:
            policy_json = json.load(f)

        # Replace placeholders in the policy
        policy_str = json.dumps(policy_json)
        for key, value in variables.items():
            placeholder = f"${{{key}}}"  # e.g., ${bucket_name}
            policy_str = policy_str.replace(placeholder, value)
            print(placeholder)
            print(value)
        # Convert the processed policy back to JSON and create a PolicyDocument
        processed_policy = json.loads(policy_str)
        try:
            policy_doc = iam.PolicyDocument.from_json(processed_policy)
        except Exception as e:
            print(f"An error occurred: {str(e)}") 
        return policy_doc

    