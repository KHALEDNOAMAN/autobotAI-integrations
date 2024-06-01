import traceback
from typing import Type, Union

import boto3, uuid
from botocore.exceptions import ClientError
from pydantic import Field

from autobotAI_integrations import AIBaseService, BaseService, list_of_unique_elements, PayloadTask, Param
from autobotAI_integrations.models import *
from autobotAI_integrations.utils.boto3_helper import Boto3Helper

class AWSBedrockIntegration(BaseSchema):
    region: str
    access_key: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)
    session_token: Optional[str] = Field(default=None, exclude=True)
    account_id: Optional[str] = None
    roleArn: Optional[str] = None
    externalId: Optional[str] = None

    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "AWS Bedrock is a service that lets you use powerful AI models from various companies for your applications, all through one place."
    )

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)

    def use_dependency(self, dependency):
        self.roleArn = dependency["roleArn"]
        self.externalId = dependency["externalId"]


class AWSBedrockService(AIBaseService):
    def __init__(self, ctx: dict, integration: Union[AWSBedrockIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AWSBedrockIntegration):
            integration = AWSBedrockIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_aws_client(self, aws_client_name: str):
        if self.integration.roleArn:
            boto3_helper = Boto3Helper(self.ctx, integration=self.integration.dump_all_data())
            return boto3_helper.get_client(aws_client_name)
        else:
            return boto3.client(
                aws_client_name,
                aws_access_key_id=self.integration.access_key,
                aws_secret_access_key=self.integration.secret_key,
                aws_session_token=self.integration.session_token
            )

    def _test_integration(self) -> dict:
        try:
            bedrock_client = self._get_aws_client('bedrock')
            models = [
                {**model, "name": model["modelId"]}
                for model in bedrock_client.list_foundation_models()["modelSummaries"]
            ]
            sts_client = self._get_aws_client("sts")
            identity_data = sts_client.get_caller_identity()
            account_id = str(identity_data['Account'])
            self.integration.account_id = account_id
            return {'success': True}
        except ClientError as e:
            print(traceback.format_exc())
            return {'success': False, 'error': traceback.format_exc()}

    def get_integration_specific_details(self) -> dict:
        try:
            bedrock_client = self._get_aws_client("bedrock")
            ec2_client = self._get_aws_client('ec2')
            regions = [region['RegionName'] for region in  ec2_client.describe_regions()["Regions"]]
            # Fetching the model
            models = [{**model, "name": model['modelId']} for model in bedrock_client.list_foundation_models()['modelSummaries']]
            return {
                "integration_id": self.integration.accountId,
                "models": models,
                "available_regions": regions
            }
        except Exception as e:
            return {
                "error": "Details can not be fetched"
            }

    @staticmethod
    def get_forms():
        return {
            "label": "AWS Bedrock",
            "type": "form",
            "children": [
                {
                    "label": "IAM Role Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "roleArn",
                            "type": "text",
                            "label": "IAM Role ARN",
                            "placeholder": "Enter IAM role ARN",
                            "required": True,
                        },
                        {
                            "name": "region",
                            "type": "select",
                            "label": "Region",
                            "placeholder": "Select Region",
                            "required": True,
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def ai_prompt_python_template():
        pass

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AWSBedrockIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        return [
            {
                "metadata": {
                    "region": self.integration.region
                },
                "clients": {
                    "bedrock": boto3.client("bedrock", region_name=self.integration.region),
                    "bedrock-runtime": boto3.client("bedrock-runtime", region_name=self.integration.region)
                },
                "params": self.prepare_params(self.filer_combo_params(payload_task.params, self.integration.region)),
                "context": payload_task.context
            }
        ]

    def filer_combo_params(self, params: List[Param], region):
        filtered_params = []
        for param in params:
            if not param.filter_relevant_resources or not param.values:
                filtered_params.append(param)
            else:
                filtered_values = []
                for value in param.values:
                    if isinstance(value, dict):
                        if value.get("region") == region:
                            filtered_values.append(value)
                    else:
                        filtered_values.append(value)
                filtered_params.append({"name": param.name, "values": filtered_values})
        return filtered_params

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = self._temp_credentials()
        return SDKCreds(envs=creds)

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def _temp_credentials(self):
        if self.integration.roleArn:
            boto3_helper = Boto3Helper(self.ctx, integration=self.integration.model_dump())
            return {
                "AWS_ACCESS_KEY_ID": boto3_helper.get_access_key(),
                "AWS_SECRET_ACCESS_KEY": boto3_helper.get_secret_key(),
                "AWS_SESSION_TOKEN": boto3_helper.get_session_token(),
            }
        else:
            return {
                "AWS_ACCESS_KEY_ID": self.integration.access_key,
                "AWS_SECRET_ACCESS_KEY": self.integration.secret_key,
                "AWS_SESSION_TOKEN": self.integration.session_token,
            }
