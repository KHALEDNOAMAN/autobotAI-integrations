from typing import List, Type, Union, Optional

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


class IPinfoIntegrations(BaseSchema):
    token: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "IPInfo"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "IPInfo.io is an API for IP address information (e.g. location)."
    )


class IPinfoService(BaseService):

    def __init__(self, ctx: dict, integration: Union[IPinfoIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, IPinfoIntegrations):
            integration = IPinfoIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get("https://ipinfo.io/8.8.8.8/json", params={
                "token": self.integration.token
            })
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False, "error": f"Request failed with status code: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False, "error": f"Request failed with error: {str(e)}"
            }

    @staticmethod
    def get_forms():
        return {
            "label": "IPInfo",
            "type": "form",
            "children": [
                {
                    "label": "API Key",
                    "type": "text",
                    "name": "token",
                    "required": False,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return IPinfoIntegrations

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.STEAMPIPE
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {}
        if self.integration.token not in [None, "None"]:
            creds["IPINFO_TOKEN"] = self.integration.token
        conf_path = "~/.steampipe/config/ipinfo.spc"
        config = """connection "ipinfo" {
  plugin = "ipinfo"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="ipinfo",
            connection_name="ipinfo",
            conf_path=conf_path,
            config=config,
        )
