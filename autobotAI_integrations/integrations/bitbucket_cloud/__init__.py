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
    username: Optional[str] = None
    password: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "BitBucket Cloud"
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        "Bitbucket Cloud is a web-based, distributed version control system."
    )

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
        # NOTE: username pass as Key and password pass as secret
        user_endpoint = "https://bitbucket.org/site/oauth2/access_token"
        try:
            auth_str = f"{self.integration.username}:{self.integration.password}"
            auth_header = "Basic " + base64.b64encode(auth_str.encode()).decode()

            response = requests.post(
                user_endpoint,
                headers={"Authorization": auth_header},
                data={
                    "grant_type": "client_credentials",
                },
            )

            if response.status_code == 200:
                return {"success": True}
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid OAuth Key/Secret or insufficient permissions.",
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Invalid Bitbucket workspace slug or API endpoint",
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
                    "label": "OAuth Consumer Key",
                    "placeholder": "OAuth Consumer Key",
                    "description": "Bitbucket Workspace OAuth Key (not username).Get from: Workspace Settings → OAuth consumers → Key",
                    "required": True,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "OAuth Consumer Secret",
                    "placeholder": "OAuth Consumer Secret",
                    "description": "Bitbucket Workspace OAuth Secret (32 chars). Get from: Workspace Settings → OAuth consumers → Secret",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
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
        CloudClass = getattr(bitbucket, "Cloud")

        user_endpoint = "https://bitbucket.org/site/oauth2/access_token"

        key = payload_task.creds.envs.get("BITBUCKET_CLOUD_KEY")
        secret = payload_task.creds.envs.get("BITBUCKET_CLOUD_SECRET")

        auth_str = f"{key}:{secret}"
        auth_header = "Basic " + base64.b64encode(auth_str.encode()).decode()

        login_request = requests.post(
            user_endpoint,
            headers={"Authorization": auth_header},
            data={
                "grant_type": "client_credentials",
            },
        )

        data = login_request.json()
        access_token = data.get("access_token")

        bitbucket_client = CloudClass(
            url="https://api.bitbucket.org/",
            token=access_token,
        )

        return [
            {
                "clients": {"bitbucket_cloud": bitbucket_client},
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        pass

    def generate_rest_api_creds(self) -> RestAPICreds:
        user_endpoint = "https://bitbucket.org/site/oauth2/access_token"

        auth_str = f"{self.integration.username}:{self.integration.password}"
        auth_header = "Basic " + base64.b64encode(auth_str.encode()).decode()

        login_request = requests.post(
            user_endpoint,
            headers={"Authorization": auth_header},
            data={
                "grant_type": "client_credentials",
            },
        )
        data = login_request.json()
        token = data.get("access_token")

        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            envs={
                "BITBUCKET_CLOUD_BASE_URL": self.integration.base_url,
                "BITBUCKET_CLOUD_KEY": self.integration.username,
                "BITBUCKET_CLOUD_SECRET": self.integration.password,
            }
        )
