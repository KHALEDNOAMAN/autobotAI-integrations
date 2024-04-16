import importlib
import os
import uuid
from typing import List, Optional

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from github import Auth


class GithubIntegration(BaseSchema):
    base_url: Optional[str] =  None# If enterprice version of gihub
    token: str = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GithubService(BaseService):

    def __init__(self, ctx, integration: GithubIntegration):
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Github",
            "type": "form",
            "children": [
                {
                    "label": "Token Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text",
                            "label": "Github Base URL",
                            "default_value": "https://<hostname/>/api/v3",
                            "description": "Github Base URL if Using Enterprise Version",
                            "required": False
                        },
                        {
                            "name": "token",
                            "type": "password",
                            "label": "Github Token",
                            "placeholder": "Enter the github token",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema():
        return GithubIntegration

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

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        github = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        
        github_auth = Auth.Token(self.integration.token)
        if self.integration.base_url:
            github_client = github.Github(auth=github_auth, base_url=self.integration.base_url)
        else:
            github_client = github.Github(auth=github_auth)
        return [
            {
                "clients": {
                    "github": github_client,
                }
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITHUB_BASE_URL": self.integration.base_url if self.integration.base_url else "",
            "GITHUB_TOKEN": self.integration.token,
        }
        conf_path = "~/.steampipe/config/github.spc"

        return SteampipeCreds(envs=envs, plugin_name="github", connection_name="github",
                              conf_path=conf_path)

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITHUB_BASE_URL": self.integration.base_url if self.integration.base_url else "",
            "GITHUB_TOKEN": self.integration.token,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
