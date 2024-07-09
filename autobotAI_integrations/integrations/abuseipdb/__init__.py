import uuid
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


class AbuseIPDBIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "AbuseIPDB is a project dedicated to helping combat the spread of hackers, spammers, and abusive activity on the internet."
    )


class AbuseIPDBService(BaseService):

    def __init__(self, ctx: dict, integration: Union[AbuseIPDBIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AbuseIPDBIntegration):
            integration = AbuseIPDBIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        url = "https://api.abuseipdb.com/api/v2/check"
        params = {"ipAddress": "118.25.6.39", "maxAgeInDays": 90, "verbose": True}
        headers = {"Key": self.integration.api_key, "Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"Error: API request failed. Status code: {response.status_code}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "AbuseIPDB",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the AbuseIPDB API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AbuseIPDBIntegration

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
            ConnectionInterfaces.REST_API
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {
            "ABUSEIPDB_API_KEY": self.integration.api_key
        }
        conf_path = "~/.steampipe/config/abuseipdb.spc"
        config = """connection "abuseipdb" {
  plugin = "abuseipdb"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="abuseipdb",
            connection_name="abuseipdb",
            conf_path=conf_path,
            config=config,
        )
