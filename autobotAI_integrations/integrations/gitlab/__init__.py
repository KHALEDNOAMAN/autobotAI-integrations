import importlib
import os
import uuid
from typing import List

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient


class GitlabIntegration(BaseSchema):
    base_url: str
    token: str = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GitlabService(BaseService):

    def __init__(self, ctx, integration: GitlabIntegration):
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Gitlab",
            "type": "form",
            "children": [
                {
                    "label": "Token Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Gitlab Base URL",
                            "default_value": "https://gitlab.com/",
                            "required": True
                        },
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Gitlab Token",
                            "placeholder": "Enter the Gitlab Token",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema():
        return GitlabIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API, ConnectionInterfaces.CLI, ConnectionInterfaces.PYTHON_SDK,
                ConnectionInterfaces.STEAMPIPE]

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
        gitlab = importlib.import_module(client_definitions[0].import_library_names[0], package=None)

        return [
            {
                "clients": {
                    "gitlab": gitlab.Gitlab(os.getenv('GITLAB_ADDR'), private_token=os.getenv('GITLAB_TOKEN'))
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITLAB_ADDR": self.integration.base_url,
            "GITLAB_TOKEN": self.integration.token,
        }
        conf_path = "~/.steampipe/config/gitlab.spc"
        config_str = """connection "gitlab" {
  plugin = "theapsgroup/gitlab"
}
"""
        return SteampipeCreds(envs=envs, plugin_name="theapsgroup/gitlab", connection_name="gitlab",
                              conf_path=conf_path, config=config_str)

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "Authorization": f"Bearer {self.integration.token}"
        }
        return RestAPICreds(api_url=self.integration.base_url, token=self.integration.token, headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITLAB_ADDR": self.integration.base_url,
            "GITLAB_TOKEN": self.integration.token,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        installer_check = "brew"
        install_command = "brew list glab || brew install glab"
        envs = {
            "GITLAB_HOST": self.integration.base_url,
            "GITLAB_TOKEN": self.integration.token,
        }
        return CLICreds(installer_check=installer_check, install_command=install_command, envs=envs)
