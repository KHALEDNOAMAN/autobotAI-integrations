import importlib
import uuid
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    CLICreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)
from atlassian import Bitbucket

from autobotAI_integrations.models import IntegrationCategory


class BitbucketIntegration(BaseSchema):
    base_url: str = Field(default="https://api.bitbucket.org")
    username: str = Field(default=None, exclude=True)
    app_password: str = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.VERSION_CONTROL.value
    description: Optional[str] = (
        "Bitbucket is a Git-based source code repository hosting service designed for teams to collaborate on code."
    )


class BitbucketService(BaseService):

    def __init__(self, ctx, integration: Union[BitbucketIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, BitbucketIntegration):
            integration = BitbucketIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            bitbucket = Bitbucket(
                url=self.integration.base_url,
                username=self.integration.username,
                password=self.integration.app_password,
            )
            user_info = bitbucket.user()
            return {"success": True, "user": user_info}
        except BaseException as e:
            return {"success": False, "error": str(e)}

    def get_integration_specific_details(self) -> dict:
        try:
            bitbucket = Bitbucket(
                url=self.integration.base_url,
                username=self.integration.username,
                password=self.integration.app_password,
            )
            repos = bitbucket.repo_list()
            return {
                "integration_id": self.integration.username,
                "repositories": [repo["name"] for repo in repos],
            }
        except Exception as e:
            return {"error": "Details cannot be fetched"}

    @staticmethod
    def get_forms():
        return {
            "label": "Bitbucket",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Bitbucket URL",
                    "placeholder": "https://api.bitbucket.org",
                    "description": "The URL of the Bitbucket instance to connect to.",
                    "required": True,
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Bitbucket Username",
                    "placeholder": "Enter Bitbucket Username",
                    "required": True,
                },
                {
                    "name": "app_password",
                    "type": "text/password",
                    "label": "App Password",
                    "placeholder": "Enter App Password",
                    "description": "The app password to use to authenticate with Bitbucket.",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema():
        return BitbucketIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        bitbucket = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        return [
            {
                "clients": {
                    "bitbucket": bitbucket.Bitbucket(
                        url=payload_task.creds.envs["BITBUCKET_URL"],
                        username=payload_task.creds.envs["BITBUCKET_USER"],
                        password=payload_task.creds.envs["BITBUCKET_APP_PASSWORD"],
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = self._temp_credentials()
        conf_path = "~/.steampipe/config/bitbucket.spc"
        config_str = """connection "bitbucket" {
  plugin = "bitbucket"
}
"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="bitbucket",
            connection_name="bitbucket",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        envs = self._temp_credentials()
        return RestAPICreds(envs=envs)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = self._temp_credentials()
        return SDKCreds(envs=envs)

    def _temp_credentials(self):
        return {
            "BITBUCKET_URL": self.integration.base_url,
            "BITBUCKET_USER": self.integration.username,
            "BITBUCKET_APP_PASSWORD": self.integration.app_password,
        }
