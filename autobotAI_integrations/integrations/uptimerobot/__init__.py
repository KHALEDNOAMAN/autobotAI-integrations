from typing import List, Type, Union

from autobotAI_integrations import list_of_unique_elements
from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import (
    BaseSchema,
    CLICreds,
    BaseService,
    ConnectionInterfaces,
)
import requests
import json


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

    def _test_integration(self, user_initiated_request: bool = False) -> dict:
        try:
            url = "https://api.uptimerobot.com/v2/getAccountDetails"
            payload = "api_key={}&format=json".format(self.integration.api_key)
            headers = {
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
            }
            response = requests.request("POST", url, data=payload, headers=headers)
            result = json.loads(response.text)
            if response.status_code == 200 and result.get('stat') == 'ok':
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": result.get('error'),
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
            ConnectionInterfaces.STEAMPIPE,
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
