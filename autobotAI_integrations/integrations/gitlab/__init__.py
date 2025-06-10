import importlib
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

from autobotAI_integrations.models import IntegrationCategory


class GitlabIntegration(BaseSchema):
    base_url: str = Field(default="https://gitlab.com/", exclude=True)
    token: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "GitLab"
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        " Version control platform similar to GitHub, offering additional features like project management and CI/CD pipelines."
    )


class GitlabService(BaseService):
    def __init__(self, ctx: dict, integration: Union[GitlabIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GitlabIntegration):
            integration = GitlabIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        from gitlab import Gitlab
        try:
            if str(self.integration.base_url) not in ["None", None]:
                gitlab = Gitlab(
                    url=str(self.integration.base_url),
                    private_token=str(self.integration.token),
                )
            else:
                gitlab = Gitlab(private_token=str(self.integration.token))
            gitlab.auth()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Gitlab",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Gitlab Base URL",
                    "placeholder": "Enter the gitlab base url if using enterprise version",
                    "default_value": "https://gitlab.com/",
                    "required": False,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "Gitlab Token",
                    "placeholder": "Enter the Gitlab Token",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema():
        return GitlabIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        gitlab = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "gitlab": gitlab.Gitlab(
                        payload_task.creds.envs["GITLAB_ADDR"],
                        private_token=payload_task.creds.envs["GITLAB_TOKEN"],
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITLAB_ADDR": str(self.integration.base_url),
            "GITLAB_TOKEN": str(self.integration.token),
        }
        conf_path = "~/.steampipe/config/gitlab.spc"
        config_str = """connection "gitlab" {
  plugin = "theapsgroup/gitlab"
}
"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="theapsgroup/gitlab",
            connection_name="gitlab",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {"Authorization": f"Bearer {str(self.integration.token)}"}
        return RestAPICreds(
            api_url=str(self.integration.base_url),
            token=str(self.integration.token),
            headers=headers,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITLAB_ADDR": str(self.integration.base_url),
            "GITLAB_TOKEN": str(self.integration.token),
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        installer_check = "brew"
        install_command = "brew list glab || brew install glab"
        envs = {
            "GITLAB_HOST": str(self.integration.base_url),
            "GITLAB_TOKEN": str(self.integration.token),
        }
        return CLICreds(
            installer_check=installer_check, install_command=install_command, envs=envs
        )
