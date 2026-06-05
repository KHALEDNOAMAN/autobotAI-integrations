from typing import Optional, Type, Union
from pydantic import Field
import requests

from autobotAI_integrations import BaseSchema, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds


class ProofpointDLPIntegration(BaseSchema):
    api_token: Optional[str] = Field(default=None, exclude=True)
    subdomain: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default="us")
    skip_test: Optional[bool] = Field(default=False)

    name: str = "Proofpoint DLP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Proofpoint Intelligent Cloud Email Security (ICES) — formerly Tessian. "
        "Provides DLP security events, user monitoring, email quarantine management, "
        "user groups, and audit trail via the Proofpoint REST API."
    )

    @property
    def base_url(self) -> str:
        subdomain = (self.subdomain or "").strip()
        if self.region == "eu":
            return f"https://{subdomain}.tessian-platform.com"
        return f"https://{subdomain}.tessian-app.com"


class ProofpointDLPService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ProofpointDLPIntegration, dict]):
        if not isinstance(integration, ProofpointDLPIntegration):
            integration = ProofpointDLPIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            if self.integration.skip_test:
                return {"success": True}
            response = requests.get(
                f"{self.integration.base_url}/api/v1/events",
                headers={
                    "Authorization": f"API-Token {self.integration.api_token}",
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
                    "error": "Invalid API token or insufficient permissions. Ensure the token owner has 'Integrations' and 'Security Events' roles.",
                }
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code} - {response.text}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Proofpoint DLP",
            "type": "form",
            "children": [
                {
                    "name": "subdomain",
                    "type": "text",
                    "label": "Subdomain",
                    "placeholder": "yourcompany",
                    "description": (
                        "The subdomain of your Proofpoint Portal. "
                        "For example, if your portal is 'https://yourcompany.tessian-app.com', "
                        "enter 'yourcompany'."
                    ),
                    "required": True,
                },
                {
                    "name": "region",
                    "type": "select",
                    "label": "Region",
                    "description": "Select your Proofpoint hosting region.",
                    "required": True,
                    "options": [
                        {"label": "US (tessian-app.com)", "value": "us"},
                        {"label": "EU (tessian-platform.com)", "value": "eu"},
                    ],
                    "default": "us",
                },
                {
                    "name": "api_token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter your Proofpoint API Token",
                    "description": (
                        "Generate from: Integrations → Security Integrations → Proofpoint API. "
                        "The token owner must have 'Integrations' and 'Security Events' roles."
                    ),
                    "required": True,
                },
                {
                    "name": "skip_test",
                    "type": "select",
                    "label": "Skip Integration Test",
                    "description": "Skip the connectivity test (useful when the API is not yet accessible).",
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
    def get_schema(ctx=None) -> Type[ProofpointDLPIntegration]:
        return ProofpointDLPIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"API-Token {self.integration.api_token}",
                "Content-Type": "application/json",
            },
        )
