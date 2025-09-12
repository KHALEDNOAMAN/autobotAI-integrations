from typing import List, Optional, Type, Union

from pydantic import Field
from autobotAI_integrations.models import IntegrationCategory, List, RestAPICreds, SteampipeCreds
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
import json


class URLScanIntegrations(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "URLScan"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "UrlScan is a free service to scan and analyse websites."
    )


class URLScanService(BaseService):

    def __init__(self, ctx: dict, integration: Union[URLScanIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, URLScanIntegrations):
            integration = URLScanIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        headers = {
            "API-Key": str(self.integration.api_key),
            "Content-Type": "application/json",
        }
        data = {"url": "https://autobot.live/", "visibility": "public"}
        response = requests.post(
            "https://urlscan.io/api/v1/scan/", headers=headers, data=json.dumps(data)
        )
        if response.status_code == 200:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "URLScan",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the URLScan API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return URLScanIntegrations

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
            # ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {"URLSCAN_API_KEY": self.integration.api_key}
        conf_path = "~/.steampipe/config/urlscan.spc"
        config = """connection "urlscan" {
  plugin  = "urlscan"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="urlscan",
            connection_name="urlscan",
            conf_path=conf_path,
            config=config
        )
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://urlscan.io",
            headers={
                "API-Key": self.integration.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )