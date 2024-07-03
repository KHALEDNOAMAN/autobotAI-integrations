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
from jira import JIRA

from autobotAI_integrations.models import IntegrationCategory


class JiraIntegration(BaseSchema):
    base_url: str = Field(default="https://jira.atlassian.com")
    username: str = Field(default=None, exclude=True)
    token: str = Field(default=None, exclude=True)
    personal_access_token: str = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "Jira is a versatile project management and issue tracking tool designed to help teams plan, track, and manage agile software development projects."
    )


class JiraService(BaseService):

    def __init__(self, ctx, integration: Union[JiraIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, JiraIntegration):
            integration = JiraIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            jira_cloud_options = {"server": self.integration.base_url}
            jira_cloud = JIRA(
                options=jira_cloud_options,
                basic_auth=(
                    self.integration.username,
                    self.integration.token or self.integration.personal_access_token,
                ),
            )
            my_account = jira_cloud.myself()
            return {"success": True}
        except BaseException as e:
            return {"success": False, "error": str(e.text)}

    @staticmethod
    def get_forms():
        return {
            "label": "Jira",
            "type": "form",
            "children": [
                {
                    "label": "Jira Cloud",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text",
                            "label": "Jira URL",
                            "placeholder": "https://jira.atlassian.com",
                            "description": "The URL of the Jira instance to connect to.",
                            "required": True
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "Jira Username",
                            "placeholder": "Enter Jira Username",
                            "required": True,
                        },
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Access Token",
                            "placeholder": "Enter Token",
                            "description": "The access token to use to authenticate with Jira cloud.",
                        },
                        {
                            "name": "personal_access_token",
                            "type": "text/password",
                            "label": "Personal Access Token",
                            "placeholder": "Enter Personal Access Token",
                            "description": "The personal access token to use to authenticate with self hosted Jira.",
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def get_schema():
        return JiraIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        jira = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        jira_cloud_options = {"server": payload_task.creds.envs["JIRA_URL"]}
        return [
            {
                "clients": {
                    "jira": jira.JIRA(
                        options=jira_cloud_options,
                        basic_auth=(
                            payload_task.creds.envs["JIRA_USER"],
                            payload_task.creds.envs["JIRA_TOKEN"] or payload_task.creds.envs["JIRA_PERSONAL_ACCESS_TOKEN"],
                        ),
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = self._temp_credentials()
        conf_path = "~/.steampipe/config/jira.spc"
        config_str = """connection "jira" {
  plugin = "jira"
}
"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="jira",
            connection_name="jira",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = self._temp_credentials()
        return SDKCreds(envs=envs)

    def _temp_credentials(self):
        envs = {
            "JIRA_URL" : self.integration.base_url,
            "JIRA_USER": self.integration.username,
        }
        if self.integration.token not in [None, "None"]:
            envs["JIRA_TOKEN"] = self.integration.token
        else:
            envs["JIRA_PERSONAL_ACCESS_TOKEN"] = self.integration.personal_access_token
        return envs
