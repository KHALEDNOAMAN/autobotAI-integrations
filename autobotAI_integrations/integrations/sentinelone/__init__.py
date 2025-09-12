from typing import Optional, Type, Union

from pydantic import Field
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
)

class SentinelOneIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, description="base url")
    token: Optional[str] = Field(default=None, description="token", exclude=True)

    name: Optional[str] = "SentinelOne"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "SentinelOne is a cloud-based cybersecurity platform that uses AI to protect organizations from threats"
    )


class SentinelOneService(BaseService):

    def __init__(self, ctx: dict, integration: Union[SentinelOneIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, SentinelOneIntegration):
            integration = SentinelOneIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        # TODO: Based on SentinelOne's API Auth method Implement this
        try:
            response = requests.get(
                url=self.integration.base_url,
                headers={
                    "Authorization": self.integration.token,  # Replace with your actual API key
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is Unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "SentinelOne",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Host URL",
                    "placeholder": "https://domain.sentinelone.net",
                    "required": True,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Your API TOKEN",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return SentinelOneIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        # TODO: Based on SentinelOne's API Auth method Implement this
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": self.integration.token,  # Replace with your actual API key
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
