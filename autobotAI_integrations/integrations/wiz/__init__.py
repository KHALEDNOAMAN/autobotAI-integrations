from typing import Type, Union

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


class WizIntegrations(BaseSchema):
    url: Optional[str] = Field(default=None, exclude=True)
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Wiz provides direct visibility, risk prioritization, and remediation guidance for development teams to address risks in their own infrastructure and applications so they can ship faster and more securely."
    )


class WizService(BaseService):

    def __init__(self, ctx: dict, integration: Union[WizIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, WizIntegrations):
            integration = WizIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # TODO: replace with actual API
            return {"success": True}
            # response = requests.get("https://api.example.com")
            # if response.status_code == 200:
            #     return {"success": True}
            # else:
            #     return {
            #     "success": False,
            #     "error": f"API request failed. Status code: {response.status_code}",
            # }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is unreachable"}

    @staticmethod
    def get_forms():
        return {
            "label": "Wiz",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text/password",
                    "label": "Client ID",
                    "placeholder": "Enter the Wiz Client ID",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter the Wiz Client Secret",
                    "required": True,
                },
                {
                    "name": "url",
                    "type": "text",
                    "label": "URL",
                    "placeholder": "Enter the Wiz URL",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return WizIntegrations

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "preview": True
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {
            "WIZ_AUTH_CLIENT_ID": self.integration.client_id,
            "WIZ_AUTH_CLIENT_SECRET": self.integration.client_secret,
            "WIZ_URL": self.integration.url,
        }
        conf_path = "~/.steampipe/config/wiz.spc"
        config = """connection "wiz" {
  plugin = "wiz"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="wiz",
            connection_name="wiz",
            conf_path=conf_path,
            config=config,
        )
