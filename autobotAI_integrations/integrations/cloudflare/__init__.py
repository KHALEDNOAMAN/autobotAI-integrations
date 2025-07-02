import importlib
from typing import Optional, Type, Union, List
from enum import Enum
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds,
    SDKCreds,
    PayloadTask,
    SDKClient,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory, SteampipeCreds

class CloudflareAuthTypes(str, Enum):
    TOKEN_INTEGRATION = "token_integration"
    GLOBAL_API_KEY_INTEGRATION = "global_api_key_integration"


class CloudflareIntegration(BaseSchema):
    email: Optional[str] = Field(default=None, exclude=False)
    api_key: Optional[str] = Field(default=None, exclude=True)

    token: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Cloudflare"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Cloudflare is a security-focused cloud services provider offering solutions like DDoS protection, web application firewall, CDN, and SSL/TLS encryption to enhance the performance and security of websites and applications."
    )


class CloudflareService(BaseService):

    def __init__(self, ctx: dict, integration: Union[CloudflareIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, CloudflareIntegration):
            integration = CloudflareIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            if self.integration.token not in ["None", None]:
                response = requests.get(
                    "https://api.cloudflare.com/client/v4/user/tokens/verify",
                    headers={
                        "Authorization": f"Bearer {self.integration.token}",
                        "Content-Type":"application/json"
                    },
                )
            else:
                response = requests.get(
                    "https://api.cloudflare.com/client/v4/user",
                    headers={
                        "X-Auth-Email": self.integration.email,
                        "X-Auth-Key": self.integration.api_key,
                        "Content-Type": "application/json",
                    },
                )

            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is unreachable"}

    @staticmethod
    def get_forms():
        return {
            "label": "Cloudflare",
            "type": "form",
            "children": [
                {
                    "label": "Token Integration(Recommended)",
                    "type": "form",
                    "formId": CloudflareAuthTypes.TOKEN_INTEGRATION.value,
                    "children": [
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Token API Key",
                            "placeholder": "Token API Key",
                            "description": "Read scope is required (write is not)",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "Global API Key Integration",
                    "type": "form",
                    "formId": CloudflareAuthTypes.GLOBAL_API_KEY_INTEGRATION.value,
                    "children": [
                        {
                            "name": "email",
                            "type": "text",
                            "label": "Email",
                            "placeholder": "example@example.com",
                            "required": True,
                        },
                        {
                            "name": "api_key",
                            "type": "text/password",
                            "label": "Api Key",
                            "placeholder": "Enter your Global API  Key",
                            "required": True,
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return CloudflareIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
            # ConnectionInterfaces.STEAMPIPE,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        if self.integration.token not in ["None", None]:
            creds = {
                "CLOUDFLARE_API_TOKEN": self.integration.token,
            }
        else:
            creds = {
                "CLOUDFLARE_EMAIL": self.integration.email,
                "CLOUDFLARE_API_KEY": self.integration.api_key,
            }
        conf_path = "~/.steampipe/config/cloudflare.spc"
        config = """connection "cloudflare" {
  plugin  = "cloudflare"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="cloudflare",
            connection_name="cloudflare",
            conf_path=conf_path,
            config=config,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {"Content-Type": "application/json"}
        
        if self.integration.token not in ["None", None]:
            headers["Authorization"] = f"Bearer {self.integration.token}"
        else:
            headers["X-Auth-Email"] = self.integration.email
            headers["X-Auth-Key"] = self.integration.api_key
            
        return RestAPICreds(
            base_url="https://api.cloudflare.com/client/v4",
            headers=headers,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {}
        
        if self.integration.token not in ["None", None]:
            envs["CLOUDFLARE_API_TOKEN"] = self.integration.token
        else:
            envs["CLOUDFLARE_EMAIL"] = self.integration.email
            envs["CLOUDFLARE_API_KEY"] = self.integration.api_key
            
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        cloudflare = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        # Initialize Cloudflare client based on available credentials
        if payload_task.creds.envs.get("CLOUDFLARE_API_TOKEN"):
            cloudflare_client = cloudflare.Cloudflare(
                api_token=payload_task.creds.envs.get("CLOUDFLARE_API_TOKEN")
            )
        else:
            cloudflare_client = cloudflare.Cloudflare(
                api_email=payload_task.creds.envs.get("CLOUDFLARE_EMAIL"),
                api_key=payload_task.creds.envs.get("CLOUDFLARE_API_KEY"),
            )
            
        return [
            {
                "clients": {
                    "cloudflare": cloudflare_client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]
