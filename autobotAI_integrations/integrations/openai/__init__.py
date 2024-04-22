import importlib
import os
import uuid
from typing import List

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient


class OpenAIIntegration(BaseSchema):
    api_key: str = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class OpenAIService(BaseService):

    def __init__(self, ctx, integration: OpenAIIntegration):
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "OpenAI",
            "type": "form",
            "children": [
                {
                    "label": "API Key Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "api_key",
                            "type": "text/password",
                            "label": "OpenAI api_key",
                            "placeholder": "Enter the OpenAI API Key",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema():
        return OpenAIIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def _test_integration(self, integration: dict):
        creds = self.generate_rest_api_creds()
        try:
            response = BaseService.generic_rest_api_call(creds, "get", "/api/v4/user")
            print(response)
            return {'success': True}
        except BaseException as e:
            return {'success': False}

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        openai = importlib.import_module(client_definitions[0].import_library_names[0], package=None)

        return [
            {
                "clients": {
                    "openai": openai.OpenAI(api_key=self.integration.api_key)
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
        }
        conf_path = "~/.steampipe/config/openai.spc"
        config_str = """connection "openai" {
  plugin = "openai"
}
"""
        return SteampipeCreds(envs=envs, plugin_name="openai", connection_name="openai",
                              conf_path=conf_path, config=config_str)

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "Authorization": f"Bearer {self.integration.api_key}"
        }
        return RestAPICreds(api_key=self.integration.api_key, headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
