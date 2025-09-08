from typing import Optional, Type, Union

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory, RestAPICreds, SteampipeCreds


class UptimeRobotIntegrations(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "UptimeRobot is a monitoring service that tracks the uptime and performance of websites, servers, and other online services."
    )


class UptimeRobotService(BaseService):

    def __init__(self, ctx: dict, integration: Union[UptimeRobotIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, UptimeRobotIntegrations):
            integration = UptimeRobotIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            url = "https://api.uptimerobot.com/v3/user/me"
            response = requests.get(
                url, headers={"Authorization": f"Bearer {self.integration.api_key}"}
            )
            response.raise_for_status()
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request Failed with Status code {response.status_code}",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed. {e}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "UptimeRobot",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the UptimeRobot API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return UptimeRobotIntegrations

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
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {"UPTIMEROBOT_API_KEY": self.integration.api_key}
        conf_path = "~/.steampipe/config/uptimerobot.spc"
        config = """connection "uptimerobot" {
  plugin = "uptimerobot"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="uptimerobot",
            connection_name="uptimerobot",
            conf_path=conf_path,
            config=config,
        )
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://api.uptimerobot.com/v3",
            headers={
                "Authorization":f"Bearer {self.integration.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
