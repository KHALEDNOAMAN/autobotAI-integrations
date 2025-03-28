from typing import Optional, Type, Union
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory, RestAPICreds, SteampipeCreds


class AbuseIPDBIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: str = "AbuseIPDB"
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
        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": "118.25.6.39", "maxAgeInDays": 90, "verbose": True},
            headers={"Key": self.integration.api_key, "Accept": "application/json"},
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

    @staticmethod
    def supported_connection_interfaces():
        return [
            # ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {"ABUSEIPDB_API_KEY": self.integration.api_key}
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
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://api.abuseipdb.com/api/v2",
            headers={
                "Key": self.integration.api_key,
                "Accept": "application/json",
            },
        )
