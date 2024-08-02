from typing import Type, Union

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


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

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
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
