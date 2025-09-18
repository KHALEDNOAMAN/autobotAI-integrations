from typing import Type, Union, Optional
from pydantic import Field
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests

from autobotAI_integrations.models import IntegrationCategory, RestAPICreds, SteampipeCreds


class IPStackIntegrations(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "IPStack"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "IPStack provides IP to geolocation APIs and global IP database services."
    )


class IPStackService(BaseService):

    def __init__(self, ctx: dict, integration: Union[IPStackIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, IPStackIntegrations):
            integration = IPStackIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            url = "http://api.ipstack.com/check"
            response = requests.get(url, params={"access_key": self.integration.api_key})

            if response.status_code == 200:
                data = response.json()
                if "success" in data and not data["success"]:
                    return {"success": False, "error": "Invalid API key"}
                else:
                    return {"success": True}
            else:
                return {"success": False, "error": f"Request failed with status code: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}

    @staticmethod
    def get_forms():
        return {
            "label": "IPStack",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API key",
                    "placeholder": "Enter the IPStack API key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return IPStackIntegrations

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces()
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            # ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        conf_path = "~/.steampipe/config/ipstack.spc"
        config = """connection "ipstack" {
  plugin = "ipstack"
}
"""
        return SteampipeCreds(
            envs={"IPSTACK_TOKEN": self.integration.api_key},
            plugin_name="ipstack",
            connection_name="ipstack",
            conf_path=conf_path,
            config=config,
        )
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="http://api.ipstack.com",
            headers={},
            query_params={"access_key": self.integration.api_key},
        )
