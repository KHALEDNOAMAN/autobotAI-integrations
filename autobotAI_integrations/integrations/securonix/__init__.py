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
        description="Securonix instance URL (e.g. https://<hostname>.securonix.net)",
    )
    token: Optional[str] = Field(default=None, exclude=True)
    test_method: Optional[str] = Field(default=None, exclude=False)
    test_api: Optional[str] = Field(default=None, exclude=False)
    skip_test: Optional[bool] = Field(default=None, exclude=False)

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
            if self.integration.skip_test:
                return {"success": True}

            test_api = self.integration.test_api or "/Snypr/ws/token/validate"
            test_method = self.integration.test_method or "get"

            response = getattr(requests, test_method)(
                f"{self.integration.base_url.rstrip('/')}{test_api}",
                headers={"token": self.integration.token},
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                error_msg = response.text.strip()
                if "<html" in error_msg.lower():
                    import re

                    title_match = re.search(
                        r"<title>([^<]+)</title>", error_msg, re.IGNORECASE
                    )
                    desc_match = re.search(
                        r"<p><b>Description</b>([^<]+)</p>", error_msg, re.IGNORECASE
                    )
                    if title_match:
                        error_msg = title_match.group(1)
                        if desc_match:
                            error_msg += f" - {desc_match.group(1).strip()}"
                return {
                    "success": False,
                    "error": f"API test failed ({response.status_code}): {error_msg}",
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
                    "label": "Host URL",
                    "placeholder": "https://<hostname>.securonix.net",
                    "description": "Securonix instance URL (e.g. https://company.securonix.net)",
                    "required": True,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter your Securonix WS API token",
                    "help_url": "https://documentation.securonix.com/bundle/securonix-snypr-6-4-user-guide/page/managing-api-tokens.html",
                    "help_url_text": "Get API Token ↗",
                    "description": "Pre-generated WS authentication token from Securonix",
                    "required": True,
                },
                {
                    "name": "test_api",
                    "type": "text",
                    "label": "Test API Path",
                    "placeholder": "API path to test integration",
                    "description": "API path to test integration (e.g. /Snypr/ws/token/validate)",
                    "required": True,
                    "default": "/Snypr/ws/token/validate",
                },
                {
                    "name": "test_method",
                    "type": "select",
                    "label": "Test HTTP Method",
                    "placeholder": "Method to hit the API with",
                    "description": "HTTP method to use for testing",
                    "required": True,
                    "options": [
                        {"label": "get", "value": "get"},
                        {"label": "post", "value": "post"},
                        {"label": "head", "value": "head"},
                    ],
                    "default": "get",
                },
                {
                    "name": "skip_test",
                    "type": "select",
                    "label": "Skip Test Integration",
                    "placeholder": "Skip the integration test",
                    "description": "If enabled, skips the integration test (useful when API is not accessible)",
                    "required": True,
                    "options": [
                        {"label": "No", "value": False},
                        {"label": "Yes", "value": True},
                    ],
                    "default": False,
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
                "Content-Type": "application/json",
            },
        )
