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

class MISPIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, description="base url")
    token: Optional[str] = Field(default=None, description="token", exclude=True)

    name: Optional[str] = "MISP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "MISP (Malware Information Sharing Platform) is an open-source threat intelligence platform designed for sharing, storing, and correlating cyber threat data among organizations and security professionals."
    )


class MISPService(BaseService):

    def __init__(self, ctx: dict, integration: Union[MISPIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, MISPIntegration):
            integration = MISPIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
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
            "label": "MISP",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Host URL",
                    "placeholder": "https://misp.local",
                    "required": True,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Your API KEY",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return MISPIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": self.integration.token,  # Replace with your actual API key
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
