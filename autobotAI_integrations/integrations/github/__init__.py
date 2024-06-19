import importlib
import os
import uuid
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from github import Auth, Github

from autobotAI_integrations.models import IntegrationCategory


class GithubIntegration(BaseSchema):
    base_url: Optional[str] =  None# If enterprise version of github
    token: str = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        "Popular version control platform for software development, known for its social coding features and large user base."
    )
    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GithubService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GithubIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GithubIntegration):
            integration = GithubIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            if self.integration.base_url:
                github = Github(self.integration.token, base_url=self.integration.base_url)
            else:
                github = Github(self.integration.token)
            user = github.get_user()
            print(f"Github Username: {user.login}")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

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
                            "type": "text/url",
                            "label": "Github Base URL",
                            "placeholder": "Enter Base URL",
                            "description": "Github Base URL if Using Enterprise Version",
                            "required": False,
                        },
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Github Token",
                            "placeholder": "Enter the github token",
                            "required": True,
                        },
                    ],
                }
            ],
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
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITHUB_BASE_URL": self.integration.base_url if self.integration.base_url else "",
            "GITHUB_TOKEN": self.integration.token,
        }
        conf_path = "~/.steampipe/config/github.spc"
        config = """connection "github" {
  plugin = "github"
}"""
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
