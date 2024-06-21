import importlib
import os
from typing_extensions import Literal
import uuid
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from pygitguardian.client import GGClient
from autobotAI_integrations.models import IntegrationCategory

class GitGuardianIntegration(BaseSchema):
    base_url: str = "https://api.gitguardian.com/v1/"
    token: str = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "GitGuardian is a security platform specifically designed to protect code repositories. "
    )

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GitGuardianService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GitGuardianIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GitGuardianIntegration):
            integration = GitGuardianIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "GitGuardian",
            "type": "form",
            "children": [
                {
                    "label": "Token Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "GitGuardian Token",
                            "placeholder": "Enter the GitGuardian token",
                            "required": True
                        }
                    ]
                }
            ]
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

    def _test_integration(self):
        try:
            client = GGClient(api_key=self.integration.token)
            if client.health_check().success:
                return {"success": True}
            else:
                return {"success": False, "error": "Invalid API Key"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        gitguardian = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        return [
            {
                "clients": {
                    "gitguardian": gitguardian.GGClient(api_key=str(self.integration.token))
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITGUARDIAN_TOKEN": str(self.integration.token),
        }
        conf_path = "~/.steampipe/config/gitguardian.spc"
        config = """connection "gitguardian" {
  plugin = "francois2metz/gitguardian"
}
"""
        return SteampipeCreds(envs=envs, plugin_name="francois2metz/gitguardian", connection_name="gitguardian",
                              conf_path=conf_path, config=config)

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "Authorization": f"Token {str(self.integration.token)}"
        }
        return RestAPICreds(api_url=self.integration.base_url, token=str(self.integration.token), headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITGUARDIAN_API_KEY": str(self.integration.token),
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
