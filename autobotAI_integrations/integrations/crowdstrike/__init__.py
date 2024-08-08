from typing import List, Type, Union

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


class CrowdstrikeIntegrations(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    client_cloud: Optional[str] = Field(default="us-2", exclude=True)

    name: Optional[str] = "CrowdStrike"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CrowdStrike provides cloud workload and endpoint security, threat intelligence, and cyberattack response services."
    )


class CrowdstrikeService(BaseService):

    def __init__(self, ctx: dict, integration: Union[CrowdstrikeIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, CrowdstrikeIntegrations):
            integration = CrowdstrikeIntegrations(**integration)
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
            "label": "Crowdstrike",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter the Client ID",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter the Client Secret",
                    "required": True,
                },
                {
                    "label": "Client Cloud",
                    "name": "client_cloud",
                    "type": "select",
                    "options": [
                        {"label": "US-1", "value": "us-1"},
                        {"label": "US-2", "value": "us-2"},
                        {"label": "EU-1", "value": "eu-1"},
                        {"label": "US-GOV-1", "value": "us-gov-1"},
                    ],
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return CrowdstrikeIntegrations

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
            "FALCON_CLIENT_ID": self.integration.client_id,
            "FALCON_CLIENT_SECRET": self.integration.client_secret,
            "FALCON_CLOUD": self.integration.client_cloud,
        }
        conf_path = "~/.steampipe/config/crowdstrike.spc"
        config = """connection "crowdstrike" {
  plugin = "crowdstrike"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="crowdstrike",
            connection_name="crowdstrike",
            conf_path=conf_path,
            config=config,
        )
