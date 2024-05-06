import traceback
from typing import Type, Union

import uuid
import boto3
import pydash
from botocore.exceptions import ClientError
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements, PayloadTask, Param
from autobotAI_integrations.models import *
from autobotAI_integrations.utils.boto3_helper import Boto3Helper


class Forms:
    pass


class AWSSDKClient(SDKClient):
    is_regional: bool


class AWSIntegration(BaseSchema):
    # TODO: Add validation for role_arn and access keys
    access_key: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)
    session_token: Optional[str] = Field(default=None, exclude=True)
    account_id: Optional[str] = None
    roleArn: Optional[str] = None
    externalId: Optional[str] = None
    activeRegions: Optional[list] = None

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class AWSService(BaseService):

    def __init__(self, ctx: dict, integration: Union[AWSIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AWSIntegration):
            integration = AWSIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            if self.integration.roleArn:
                boto3_helper = Boto3Helper(self.ctx, integration=self.integration.dump_all_data())
                boto3_helper.get_client("ec2")
            else:
                iam_client = boto3.client(
                    "iam",
                    aws_access_key_id=self.integration.access_key,
                    aws_secret_access_key=self.integration.secret_key,
                    aws_session_token=self.integration.session_token
                )
                response = iam_client.get_account_summary(max_items=10)
            return {'success': True}
        except ClientError as e:
            print(traceback.format_exc())
            return {'success': False, 'error': traceback.format_exc()}

    @staticmethod
    def get_forms():
        return {
            "label": "AWS",
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
                        }
                    ]
                },
                {
                    "label": "AccessKey / SecretKey Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "access_key",
                            "type": "text",
                            "label": "Access Key",
                            "placeholder": "Enter your AWS access key",
                            "required": True
                        },
                        {
                            "name": "secret_key",
                            "type": "text/password",
                            "label": "Secret Key",
                            "placeholder": "Enter your AWS secret key",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AWSIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": "print('hello world')"
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/aws.spc"
        config = """connection "aws" {
  plugin = "aws"
  ignore_error_codes = ["AccessDenied", "AccessDeniedException", "NotAuthorized", "UnauthorizedOperation", "UnrecognizedClientException", "AuthorizationError"]
}
"""
        return SteampipeCreds(envs=creds, plugin_name="aws", connection_name="aws",
                              conf_path=conf_path, config=config)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        built_clients = {
            "global": {},
            "regional": {

                }
            }
        global_clients = pydash.filter_(client_definitions, lambda x: x.is_regional is False)
        regional_clients = pydash.filter_(client_definitions, lambda x: x.is_regional is True)
        if global_clients:
            for client in global_clients:
                built_clients["global"][client.name] = boto3.client(client.name)

        active_regions = self.integration.activeRegions
        if not active_regions:
            active_regions = ["us-east-1"]
        for region in active_regions:
            built_clients["regional"].setdefault(region, {})
            for client in regional_clients:
                try:
                    built_clients["regional"][region][client.name] = boto3.client(client.name, region_name=region)
                except ImportError:
                    print(f"Failed create client for {client['name']}")
        combinations = []
        if built_clients["regional"]:
            for region in built_clients["regional"]:
                combo = {"metadata": {
                    "region": region
                }, "clients": {**built_clients["global"], **built_clients["regional"][region]},
                    "params": self.prepare_params(self.filer_combo_params(payload_task.params, region)),
                    "context": payload_task.context}
                combinations.append(combo)
        return combinations

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
        return [ConnectionInterfaces.REST_API, ConnectionInterfaces.CLI, ConnectionInterfaces.PYTHON_SDK,
                ConnectionInterfaces.STEAMPIPE]

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
