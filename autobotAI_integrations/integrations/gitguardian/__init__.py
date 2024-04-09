import importlib
import os
import uuid
from typing import List

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient


class GitGuardianIntegration(BaseSchema):
    base_url: str = "https://api.gitguardian.com/v1/"
    token: str = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GitGuardianService(BaseService):

    def __init__(self, ctx, integration: GitGuardianIntegration):
        super().__init__(ctx, integration)

    def get_forms(self):
        return {
            "token_form": {
                "fields": [
                    {
                        "name": "token",
                        "type": "password",
                        "label": "GitGuardian Token",
                        "placeholder": "Enter the GitGuardian token",
                        "required": True
                    }
                ],
                "submit_label": "Submit"
            }
        }

    @staticmethod
    def get_schema():
        return GitGuardianIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def _test_integration(self, integration: dict):
        pass
    
    def _get_clients(self, client_definations: List[SDKClient]):
        client_classes = dict()
        for client in client_definations:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    client_classes[client.class_name] = cls(api_key=self.integration.token)
            except BaseException as e:
                print(e)
                continue
        return client_classes

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        clients = self._get_clients(client_definitions)
        return [
            {
                "clients": clients
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITGUARDIAN_TOKEN": self.integration.token,
        }
        conf_path = "~/.steampipe/config/gitguardian.spc"
        return SteampipeCreds(envs=envs, plugin_name="francois2metz/gitguardian", connection_name="gitguardian",
                              conf_path=conf_path)

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "Authorization": f"Token {self.integration.token}"
        }
        return RestAPICreds(api_url=self.integration.base_url, token=self.integration.token, headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITGUARDIAN_API_KEY": self.integration.token,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
