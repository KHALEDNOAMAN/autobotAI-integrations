from typing import Optional, Type, Union

import requests
from pydantic import Field, field_validator

from autobotAI_integrations import BaseSchema, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds


class CyberMindrIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: Optional[str] = Field(default=None)

    name: str = "CyberMindr"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CyberMindr is a Continuous Threat Exposure Management (CTEM) and Attack Path Discovery platform. "
        "It automates external asset discovery, validates vulnerabilities across 30+ OSINT sources, "
        "and provides risk-prioritised remediation guidance accessible via REST API, PDF, and XLS formats."
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            raise ValueError(
                "base_url is required and cannot be empty. "
                "Enter your CyberMindr tenant URL (e.g. https://app.cybermindr.com)."
            )
        return v.strip().rstrip("/")


class CyberMindrService(BaseService):
    def __init__(self, ctx: dict, integration: Union[CyberMindrIntegration, dict]):
        if not isinstance(integration, CyberMindrIntegration):
            integration = CyberMindrIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # TODO (senior): Validate the exact test endpoint path against your tenant's
            # Swagger UI (typically at {base_url}/swagger or {base_url}/api/docs).
            # Current path is inferred from public CyberMindr platform documentation.
            response = requests.get(
                f"{self.integration.base_url}/api/v1/assets",
                headers={
                    "Authorization": f"Bearer {self.integration.api_key}",
                    "Content-Type": "application/json",
                },
                params={"limit": 1},
                timeout=15,
            )
            if response.status_code == 200:
                return {"success": True}
            if response.status_code in (401, 403):
                return {
                    "success": False,
                    "error": (
                        "Invalid API key or insufficient permissions. "
                        "Ensure the API key is generated from your CyberMindr dashboard "
                        "under Settings → API."
                    ),
                }
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code} - {response.text}",
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": (
                    "Unable to reach the CyberMindr platform. "
                    "Please verify the base_url is correct and reachable."
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "CyberMindr",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Base URL",
                    "placeholder": "https://app.cybermindr.com",
                    "description": (
                        "The URL of your CyberMindr tenant platform. "
                        "This is the address you use to access the CyberMindr dashboard."
                    ),
                    "required": True,
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your CyberMindr API Key",
                    "description": (
                        "Generate your API key from the CyberMindr dashboard: "
                        "Settings → API → Generate New API Key."
                    ),
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[CyberMindrIntegration]:
        return CyberMindrIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "preview": True,
        }

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {self.integration.api_key}",
                "Content-Type": "application/json",
            },
        )
