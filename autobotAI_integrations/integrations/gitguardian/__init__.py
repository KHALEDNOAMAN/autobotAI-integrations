import importlib
import requests
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient

from autobotAI_integrations.models import IntegrationCategory


class GitGuardianIntegration(BaseSchema):
    base_url: str = "https://api.gitguardian.com/v1/"
    token: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "GitGuardian"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "GitGuardian is a security platform specifically designed to protect code repositories. "
    )


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
                    "name": "token",
                    "type": "text/password",
                    "label": "GitGuardian Token",
                    "placeholder": "Enter the GitGuardian token",
                    "required": True,
                }
            ],
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
            # ConnectionInterfaces.STEAMPIPE
        ]

    def _test_integration(self):
        try:
            response = requests.get(
                "https://api.gitguardian.com/v1/health",
                headers={"authorization": f"Token {self.integration.token}"},
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": "Invalid API Key"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        gitguardian = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        return [
            {
                "clients": {
                    "gitguardian": gitguardian.GGClient(
                        api_key=payload_task.creds.envs.get("GITGUARDIAN_API_KEY")
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
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
        return SteampipeCreds(
            envs=envs,
            plugin_name="francois2metz/gitguardian",
            connection_name="gitguardian",
            conf_path=conf_path,
            config=config,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "authorization": f"Token {str(self.integration.token)}"
        }
        return RestAPICreds(base_url=self.integration.base_url.strip("/v1/"), headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITGUARDIAN_API_KEY": str(self.integration.token),
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
