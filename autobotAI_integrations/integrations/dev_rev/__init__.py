from typing import Optional, Type, Union
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import (
    IntegrationCategory,
    RestAPICreds,
)


class DevRevIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: str = "DevRev"
    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "DevRev is a platform that helps developers and revenue teams work together to build products customers love."
    )


class DevRevService(BaseService):
    def __init__(self, ctx: dict, integration: Union[DevRevIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, DevRevIntegration):
            integration = DevRevIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        response = None
        try:
            response = requests.get(
                "https://api.devrev.ai/dev-users.self",
                headers={
                    "Authorization": self.integration.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            response.raise_for_status()

            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "DevRev",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the DevRev API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return DevRevIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://api.devrev.ai",
            headers={
                "Authorization": self.integration.api_key,
            },
        )
