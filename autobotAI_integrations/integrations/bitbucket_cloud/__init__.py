import base64
import importlib
from typing import List, Optional, Union

import requests

from pydantic import Field, field_validator

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)

from autobotAI_integrations.models import IntegrationCategory


class BitBucketCloudIntegration(BaseSchema):
    base_url: str = Field(default="https://api.bitbucket.org/2.0")
    username: str = Field(default=None, exclude=True)
    password: str = Field(default=None, exclude=True)

    name: Optional[str] = "BitBucket Cloud"
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = "Bitbucket Cloud is a web-based, distributed version control system."

    @classmethod
    @field_validator("base_url")
    def validate_base_url(cls, v):
        if v is None or v.strip() == "":
            return "https://api.bitbucket.org/2.0"
        return v.rstrip("/")


class BitBucketCloudService(BaseService):
    def __init__(self, ctx: dict, integration: Union[BitBucketCloudIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, BitBucketCloudIntegration):
            integration = BitBucketCloudIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        # NOTE: o test the integration, we need to get the user read permission
        user_endpoint = f"{self.integration.base_url}/user"
        try:
            response = requests.get(user_endpoint, auth=(self.integration.username, self.integration.password))

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
            "label": "Bitbucket Cloud",
            "type": "form",
            "children": [
                {
                    "name": "username",
                    "type": "text",
                    "label": "Username",
                    "placeholder": "e.g., your Bitbucket Cloud username",
                    "description": "The Bitbucket Cloud account username used for API authentication.",
                    "required": True,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "App Password",
                    "placeholder": "Enter your Bitbucket App password",
                    "description": "Provide an App password with 'account:read' permission. Required for authenticating your Bitbucket Cloud account securely.",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema():
        return BitBucketCloudIntegration
    
    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

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
                    "bitbucket_cloud": bitbucket.Cloud(
                        username=payload_task.creds.envs.get("BITBUCKET_CLOUD_USERNAME"),
                        password=payload_task.creds.envs.get("BITBUCKET_CLOUD_PASSWORD"),
                        cloud=True
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        pass

    def generate_rest_api_creds(self) -> RestAPICreds:
        encoded_credentials = base64.b64encode(
            f"{self.integration.username}:{self.integration.password}".encode(
                "utf-8"
            )
        ).decode("utf-8")
        return RestAPICreds(
            base_url=self.integration.base_url.rstrip("/"),
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            verify_ssl=self.integration.base_url.split("://")[0] == "https",
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            envs={
                "BITBUCKET_CLOUD_BASE_URL": self.integration.base_url,
                "BITBUCKET_CLOUD_USERNAME": self.integration.username,
                "BITBUCKET_CLOUD_PASSWORD": self.integration.password,
            }
        )
