import traceback
from typing import Type, Union

import boto3, uuid
from botocore.exceptions import ClientError
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements, PayloadTask, Param
from autobotAI_integrations.models import *
from autobotAI_integrations.utils.boto3_helper import Boto3Helper


class AwsSesIntegration(BaseSchema):
    region: str
    access_key: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)
    session_token: Optional[str] = Field(default=None, exclude=True)
    account_id: Optional[str] = None
    roleArn: Optional[str] = None
    externalId: Optional[str] = None

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)

    def use_dependency(self, dependency):
        self.roleArn = dependency["roleArn"]
        self.externalId = dependency["externalId"]


class AwsSesService(BaseService):

    def __init__(self, ctx: dict, integration: Union[AwsSesIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AwsSesIntegration):
            integration = AwsSesIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, integration: dict) -> dict:
        res = None
        try:
            boto3_helper = Boto3Helper(integration=integration)
            boto3_helper.get_client("ses")
            res = {'success': True}
        except ClientError as e:
            print(traceback.format_exc())
            if 'AccessDenied' in str(e):
                res = {'success': False, 'error': repr(e)}
        return res

    @staticmethod
    def get_forms():
        return {
            "label": "AWS SES",
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
                            "required": True
                        },
                        {
                            "name": "region",
                            "type": "select",
                            "label": "Region",
                            "placeholder": "Select Region",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AwsSesIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": "print('hello world')"
        }

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        return [
            {
                "metadata": {
                    "region": self.integration.region
                },
                "clients": {
                    "ses": boto3.client("ses", region_name=self.integration.region)
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
        boto3_helper = Boto3Helper(self.ctx, integration=self.integration.model_dump())
        return {
            "AWS_ACCESS_KEY_ID": boto3_helper.get_access_key(),
            "AWS_SECRET_ACCESS_KEY": boto3_helper.get_secret_key(),
            "AWS_SESSION_TOKEN": boto3_helper.get_session_token(),
        }
