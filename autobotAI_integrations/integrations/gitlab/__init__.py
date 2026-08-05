import importlib
import re
from typing import List, Optional, Union
from urllib.parse import urlparse

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

from autobotAI_integrations.models import IntegrationCategory, MCPCreds


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
                    "help_url": "https://gitlab.com/-/profile/personal_access_tokens",
                    "help_url_text": "Generate Token ↗",
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return GitlabIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.MCP_SERVER,
            # ConnectionInterfaces.STEAMPIPE,
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
        headers = {"PRIVATE-TOKEN": str(self.integration.token)}
        base_url = str(self.integration.base_url).rstrip("/")
        # GitLab serves its REST API at <host>/api/v4 on gitlab.com AND on every
        # self-managed instance. This used to append the path only when the URL
        # started with "https://gitlab.com", so a self-managed instance had all
        # of its REST calls aimed at the web UI root instead of the API — which
        # returns HTML/404 and surfaces as a generic failure. Note the old check
        # was also a plain prefix match, so "https://gitlab.company.com" matched
        # it by accident while "https://git.company.com" did not.
        #
        # Tolerate a user who already typed the API path so we never double it.
        if not re.search(r"/api/v\d+$", base_url):
            base_url = f"{base_url}/api/v4"
        return RestAPICreds(
            base_url=base_url,
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

    @staticmethod
    def _is_public_gitlab_host(base_url: str) -> bool:
        parsed = urlparse(str(base_url or ""))
        return parsed.scheme.lower() == "https" and (parsed.hostname or "").lower() == "gitlab.com"

    def generate_mcp_creds(self) -> MCPCreds:
        # Autobot GitLab integrations authenticate with a user-provided PAT.
        # MCP uses the same token; host is restricted to exact gitlab.com.
        #
        # This restriction is deliberate and must stay until MCP server URLs can
        # be resolved per integration: the URLs in mcp_servers.json are loaded by
        # get_all_mcp_server_actions(), a classmethod with no access to this
        # instance, so they are hardcoded to https://gitlab.com/api/v4/mcp.
        # Letting a self-managed integration through would send that customer's
        # private token to gitlab.com.
        #
        # Raise something the caller can identify and show, rather than a bare
        # Exception that reaches the user as "something went wrong".
        if not self._is_public_gitlab_host(self.integration.base_url):
            host = urlparse(str(self.integration.base_url or "")).hostname or "(unset)"
            raise ValueError(
                f"GitLab MCP is only available for gitlab.com, but this "
                f"integration points at '{host}'. Self-managed GitLab needs "
                f"per-instance MCP server URLs, which are not supported yet — "
                f"the other GitLab connection types (REST, SDK, CLI, Steampipe) "
                f"work normally against this host."
            )

        return MCPCreds(
            headers={
                "Authorization": f"Bearer {self.integration.token}",
            },
        )
