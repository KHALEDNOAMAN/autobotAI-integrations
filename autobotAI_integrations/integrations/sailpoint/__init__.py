import importlib
from typing import List, Optional, Union

from pydantic import Field
import requests

from autobotAI_integrations import (
    BaseSchema,
    RestAPICreds,
    SDKCreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)

from autobotAI_integrations.models import IntegrationCategory


class SailPointIndentityNowIntegration(BaseSchema):
    tenantname: Optional[str] = Field(default=None, description="Tenant Name")
    tenantdomain: Optional[str] = Field(default=None, description="Tenant Domain")
    username: Optional[str] = Field(default=None, exclude=False)
    password: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = "Sailpoint"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "SailPoint is a leading identity security and identity governance and administration platform that helps organizations manage and secure user access to applications and data."
    )


class SailPointIdentityNowService(BaseService):
    def __init__(
        self, ctx: dict, integration: Union[SailPointIndentityNowIntegration, dict]
    ):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, SailPointIndentityNowIntegration):
            integration = SailPointIndentityNowIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        if (
            self.integration.tenantname
            and self.integration.tenantdomain
            and self.integration.username
            and self.integration.password
        ):
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            user_endpoint = f"https://{self.integration.tenantname}.api.{self.integration.tenantdomain}.com/oauth/token"

            try:
                response = requests.post(
                    user_endpoint,
                    headers=headers,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.integration.username,
                        "client_secret": self.integration.password,
                    },
                )
                if response.status_code == 200:
                    return {"success": True}
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Authentication failed. Please check your ClientId and Client Secret.",
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": "Error: Not Found. Invalid Tenant Name or Tenant Url",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Authentication failed with status code: {response.status_code}",
                    }
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "No authentication credentials provided"}

    @staticmethod
    def get_forms():
        return {
            "label": "SailPoint",
            "type": "form",
            "children": [
                {
                    "label": "SailPoint Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "tenantname",
                            "type": "text",
                            "label": "SailPoint Tenant Name",
                            "placeholder": "https://<tenant>identitynow.com",
                            "description": "Enter the Tenant name",
                            "required": True,
                        },
                        {
                            "name": "tenantdomain",
                            "type": "text",
                            "label": "SailPoint Tenant URL",
                            "placeholder": "https://<tenant>.identitynow.com (or .identitynow-demo.com)",
                            "description": "Enter your SailPoint IdentityNow Tenant URL",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "ClientId",
                            "placeholder": "Enter your SailPoint ClientId",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Client Secret",
                            "placeholder": "Enter your SailPoint Client Secret",
                            "required": True,
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return SailPointIndentityNowIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API, ConnectionInterfaces.PYTHON_SDK]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> List:
        sailpoint = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        client_id = payload_task.creds.envs.get("SAILPOINT_CLIENTID")
        client_secret = payload_task.creds.envs.get("SAILPOINT_CLIENT_SECRET")
        tenant_name = payload_task.creds.envs.get("SAILPOINT_TENANTNAME")
        tenant_domain = payload_task.creds.envs.get("SAILPOINT_TENANTDOMAIN")
        base_url = f"https://{tenant_name}.api.{tenant_domain}.com"
        token_url = f"https://{tenant_name}.api.{tenant_domain}.com/oauth/token"

        config = sailpoint.Configuration()
        config.client_id = client_id
        config.client_secret = client_secret
        config.base_url = base_url
        config.experimental = True
        config.token_url = token_url

        token_response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        access_token = token_response.json().get("access_token")
        config.access_token = access_token

        sailpoint_client = sailpoint.ApiClient(config)

        return [
            {
                "clients": {
                    "sailpoint": sailpoint_client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_rest_api_creds(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        user_endpoint = f"https://{self.integration.tenantname}.api.{self.integration.tenantdomain}.com/oauth/token"
        response = requests.post(
            user_endpoint,
            headers=headers,
            data={
                "grant_type": "client_credentials",
                "client_id": self.integration.username,
                "client_secret": self.integration.password,
            },
        )
        data = response.json()
        token = data.get("access_token")
        return RestAPICreds(
            base_url=f"https://{self.integration.tenantname}.api.{self.integration.tenantdomain}.com/v2025",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    def generate_python_sdk_creds(self):
        envs = {
            "SAILPOINT_TENANTNAME": self.integration.tenantname,
            "SAILPOINT_TENANTDOMAIN": self.integration.tenantdomain,
            "SAILPOINT_CLIENTID": self.integration.username,
            "SAILPOINT_CLIENT_SECRET": self.integration.password,
        }
        return SDKCreds(envs=envs)
