import json
import aws_cdk as core

class ParameterLoader:
    def __init__(self, stack: core.Stack, file_path: str):
        """
        Initialize the parameter loader.

        :param stack: The CDK stack where parameters will be created.
        :param file_path: Path to the CloudFormation parameters file (JSON format).
        """
        self.stack = stack
        self.file_path = file_path
        
    def load_cfn_parameters(self) -> dict:
        """
        Load parameters from a CloudFormation parameters JSON file.

        :param file_path: Path to the JSON file containing parameters.
        :return: Dictionary of parameter names and CfnParameter objects.
        """
        try:
            with open(self.file_path, "r") as file:
                parameter_data = json.load(file)["parameters"]

            cfn_parameters = {}
            for param_name, param_value in parameter_data.items():
                cfn_parameters[param_name] = core.CfnParameter(
                    self.stack, param_name, type="String", default=param_value
                )
            return cfn_parameters
        except Exception as e:
            raise ValueError(f"Failed to load parameters from {self.file_path}: {e}")

    def load_parameters(self) -> dict:
        """
        Load parameters from a CloudFormation parameters JSON file.

        :param file_path: Path to the JSON file containing parameters.
        :return: Dictionary of parameter names and CfnParameter objects.
        """
        try:
            with open(self.file_path, "r") as file:
                parameter_data = json.load(file)["parameters"]

            parameters = {}
            for param_name, param_value in parameter_data.items():
                parameters[param_name] = param_value
            return parameters
        except Exception as e:
            raise ValueError(f"Failed to load parameters from {self.file_path}: {e}")
        
    def get_parameter(self, name: str) -> core.CfnParameter:
        """
        Retrieve a CfnParameter object by name.

        :param name: The name of the parameter.
        :return: The corresponding CfnParameter object.
        """
        if name not in self.parameters:
            raise KeyError(f"Parameter {name} not found.")
        return self.parameters[name]