import importlib
import re
import jwt
import time
from typing import List, Optional, Union

from pydantic import Field, field_validator
import requests

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient

from autobotAI_integrations.models import IntegrationCategory


class GithubIntegration(BaseSchema):
    base_url: str =  Field(default="https://api.github.com")# If enterprise version of github
    token: Optional[str] = Field(default=None, exclude=True)
    installation_id: Optional[str] = Field(default=None)
    app_id: str = Field(default="1857214")
    private_key: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = "GitHub"
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        "Popular version control platform for software development, known for its social coding features and large user base."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, base_url) -> Optional[str]:
        public_github_pattern = r"^https://api\.github\.com/?$"
        enterprise_github_pattern = r"^https://github\.[\w.-]+\.com/api/v3/?$"
        if base_url and base_url != "None":
            if re.match(public_github_pattern, base_url) or re.match(
                enterprise_github_pattern, base_url
            ):
                return base_url.strip("/")
            raise ValueError("Invalid GitHub Base URL {}".format(base_url))
        return "https://api.github.com"


class GithubService(BaseService):
    def __init__(self, ctx: dict, integration: Union[GithubIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GithubIntegration):
            integration = GithubIntegration(**integration)
        super().__init__(ctx, integration)
        self.token = integration.token
        if not self.token and integration.installation_id:
            self.token = self.get_installation_token(integration.installation_id, self.integration.private_key_url or ctx.get("integration_extra_details", {}).get("github_app_integration_private_key"), self.integration.app_id)

    def _generate_jwt(self, private_key, app_id) -> str:
        now = int(time.time())
        payload = {
            "iat": now - 60,     # issued at
            "exp": now + 600,    # 10 minutes expiration
            "iss": app_id        # GitHub App ID
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def get_installation_token(self, installation_id, private_key, app_id) -> str:
        jwt_token = self._generate_jwt(private_key, app_id)
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json"
        }
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["token"]

    def _test_integration(self):
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

        # Try accessing the user endpoint to validate the token and URL
        user_endpoint = f"{self.integration.base_url}/user"

        try:
            response = requests.get(user_endpoint, headers=headers)

            if response.status_code == 200:
                return {"success": True}
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Error: Unauthorized. Invalid token or token does not have access to this GitHub instance.",
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Error: Not Found. Invalid GitHub URL or endpoint.",
                }
            else:
                return {
                    "success": False,
                    "error": f"Error: Unexpected status code {response.status_code}. Response: {response.text}",
                }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Github",
            "type": "form",
            "children": [
                {
                    "label": "PAT Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Github Base URL",
                            "placeholder": "Enter Base URL default: https://api.github.com",
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
                },
                {
                    "label": "App Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Github Base URL",
                            "placeholder": "Enter Base URL default: https://api.github.com",
                            "description": "Github Base URL if Using Enterprise Version",
                            "required": False,
                        },
                        {
                            "name": "installation_id",
                            "type": "text/password",
                            "label": "Installation ID",
                            "placeholder": "Enter the Installation Id",
                            "description": "The Installation ID Generated after Installing the Github APP",
                            "required": True,
                        },
                        {
                            "name": "app_id",
                            "type": "text",
                            "label": "App ID",
                            "placeholder": "Leave Empty or '1857214' for Official App or Add your custom app's App Id",
                            "description": "The App ID Generated after creating the Github APP",
                            "required": False,
                        },
                        {
                            "name": "private_key",
                            "type": "text/password",
                            "label": "Private Key",
                            "placeholder": "Leave Empty for official github app or add your custom private key",
                            "description": "The Private Key Required to generate Access Tokens",
                            "required": False,
                        },
                    ],
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
            # ConnectionInterfaces.STEAMPIPE
        ]

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        github = importlib.import_module(client_definitions[0].import_library_names[0], package=None)

        github_client = github.Github(
            payload_task.creds.envs.get("GITHUB_TOKEN"),
            base_url=payload_task.creds.envs.get("GITHUB_BASE_URL"),
        )
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
            "GITHUB_TOKEN": str(self.token),
        }
        if re.match(
            r"^https://github\.[\w.-]+\.com/api/v3/?$", self.integration.base_url
        ):
            envs["GITHUB_BASE_URL"] = self.integration.base_url
        conf_path = "~/.steampipe/config/github.spc"
        config = """connection "github" {
  plugin = "github"
}"""
        return SteampipeCreds(envs=envs, plugin_name="github", connection_name="github",
                              conf_path=conf_path, config=config)

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "GITHUB_BASE_URL": self.integration.base_url,
            "GITHUB_TOKEN": self.token
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
