from typing import Optional, Type, Union

import requests
from pydantic import Field, field_validator

from autobotAI_integrations import BaseSchema, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds

ORCA_REGION_URLS = {
    "us": "https://api.orcasecurity.io",
    "eu": "https://app.eu.orcasecurity.io",
    "au": "https://app.au.orcasecurity.io",
    "in": "https://app.in.orcasecurity.io",
    "il": "https://app.il.orcasecurity.io",
}


class OrcaSecurityIntegration(BaseSchema):
    api_token: str = Field(..., exclude=True)
    base_url: Optional[str] = Field(
        default="https://api.orcasecurity.io",
        description="Orca Security tenant URL — region-specific.",
    )

    name: str = "Orca Security"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Orca Security is an agentless Cloud-Native Application Protection Platform (CNAPP) "
        "that provides full-stack visibility across AWS, Azure, GCP, Oracle Cloud, and Alibaba Cloud. "
        "It detects vulnerabilities, misconfigurations, malware, IAM risks, lateral movement risks, "
        "and sensitive data exposure — all without deploying agents."
    )

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            raise ValueError(
                "base_url is required. Enter your Orca Security tenant URL "
                "(e.g. https://api.orcasecurity.io for US)."
            )
        return v.strip().rstrip("/")


class OrcaSecurityService(BaseService):

    def __init__(self, ctx: dict, integration: Union[OrcaSecurityIntegration, dict]):
        if not isinstance(integration, OrcaSecurityIntegration):
            integration = OrcaSecurityIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(
                f"{self.integration.base_url}/api/query/alerts",
                headers={
                    "Authorization": f"Bearer {self.integration.api_token}",
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
                        "Invalid API token or insufficient permissions. "
                        "Ensure the token is generated from Settings → Integrations → API Tokens "
                        "and has at least the Viewer role."
                    ),
                }
            return {
                "success": False,
                "error": (
                    f"Request failed with status code: {response.status_code} — {response.text}"
                ),
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": (
                    "Unable to reach the Orca Security platform. "
                    "Please verify the Base URL is correct and matches your region."
                ),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Orca Security",
            "type": "form",
            "children": [
                {
                    "name": "api_token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter your Orca Security API Token",
                    "description": (
                        "Generate your API token from the Orca dashboard: "
                        "Settings → Integrations → API Tokens → Add API Token. "
                        "Assign at least the Viewer role."
                    ),
                    "required": True,
                },
                {
                    "name": "base_url",
                    "type": "select",
                    "label": "Region / Base URL",
                    "description": (
                        "Select the region that matches your Orca Security tenant."
                    ),
                    "options": [
                        {"label": "US (api.orcasecurity.io)", "value": "https://api.orcasecurity.io"},
                        {"label": "Europe (app.eu.orcasecurity.io)", "value": "https://app.eu.orcasecurity.io"},
                        {"label": "Australia (app.au.orcasecurity.io)", "value": "https://app.au.orcasecurity.io"},
                        {"label": "India (app.in.orcasecurity.io)", "value": "https://app.in.orcasecurity.io"},
                        {"label": "Israel (app.il.orcasecurity.io)", "value": "https://app.il.orcasecurity.io"},
                    ],
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[OrcaSecurityIntegration]:
        return OrcaSecurityIntegration

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
                "Authorization": f"Bearer {self.integration.api_token}",
                "Content-Type": "application/json",
            },
        )
