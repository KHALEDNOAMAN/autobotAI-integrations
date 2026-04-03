from typing import Optional, Type, Union

import requests
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds


class SecuronixIntegration(BaseSchema):
    base_url: Optional[str] = Field(
        default=None,
        description="Securonix SNYPR base URL (e.g. https://<hostname>/Snypr)",
    )
    token: Optional[str] = Field(default=None, exclude=True)

    name: str = "Securonix"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Securonix Unified Defense SIEM is a cloud-native security analytics platform "
        "that combines SIEM, UEBA, and SOAR capabilities for advanced threat detection, "
        "investigation, and automated response."
    )


class SecuronixService(BaseService):
    def __init__(self, ctx: dict, integration: Union[SecuronixIntegration, dict]):
        """
        Integration should have all the data regarding the integration.
        """
        if not isinstance(integration, SecuronixIntegration):
            integration = SecuronixIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(
                f"{self.integration.base_url.rstrip('/')}/ws/token/validate",
                headers={"token": self.integration.token},
            )
            if response.status_code == 200 and response.text.strip().lower() == "valid":
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Token validation failed ({response.status_code}): {response.text.strip()}",
                }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection is unreachable. Verify the base URL is correct.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Securonix",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Base URL",
                    "placeholder": "https://<hostname>/Snypr",
                    "description": "Securonix SNYPR base URL in the format https://<hostname or IP>/Snypr",
                    "required": True,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter your Securonix WS API token",
                    "description": "Pre-generated WS authentication token from Securonix",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return SecuronixIntegration

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
                "token": self.integration.token,
                "Accept": "application/vnd.snypr.app-v6.0+json",
                "Content-Type": "application/json",
            },
        )
