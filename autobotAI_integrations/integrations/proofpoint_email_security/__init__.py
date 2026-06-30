from pydantic import Field
import requests

from typing import Optional, Type, Union

from autobotAI_integrations import BaseSchema, RestAPICreds, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import IntegrationCategory


class ProofpointEmailSecurityIntegration(BaseSchema):
    principal: str = Field(
        default=None,
        exclude=True,
        description="The Service Principal client ID generated in the TAP dashboard."
    )
    secret: str = Field(
        default=None,
        exclude=True,
        description="The Secret associated with the principal."
    )

    name: str = "Proofpoint Email Security"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = "Proofpoint Targeted Attack Protection (TAP) integration for SIEM, forensics, and campaigns."


class ProofpointEmailSecurityService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ProofpointEmailSecurityIntegration, dict]):
        if not isinstance(integration, ProofpointEmailSecurityIntegration):
            integration = ProofpointEmailSecurityIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ProofpointEmailSecurityIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "Proofpoint Email Security",
            "type": "form",
            "children": [
                {
                    "name": "principal",
                    "type": "text",
                    "label": "Service Principal",
                    "placeholder": "Enter your Service Principal ID",
                    "required": True,
                    "help_url": "https://help.proofpoint.com/Threat_Insight_Dashboard/API_Documentation/Overview",
                    "help_url_text": "Proofpoint API Docs ↗",
                },
                {
                    "name": "secret",
                    "type": "text/password",
                    "label": "Secret",
                    "placeholder": "Enter your Service Principal Secret",
                    "required": True,
                    "help_url": "https://help.proofpoint.com/Threat_Insight_Dashboard/API_Documentation/Overview",
                    "help_url_text": "Proofpoint API Docs ↗",
                }
            ],
        }

    @staticmethod
    def get_category() -> str:
        return IntegrationCategory.SECURITY_TOOLS.value

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://tap-api-v2.proofpoint.com/v2",
            auth=(self.integration.principal, self.integration.secret)
        )

    def _test_integration(self) -> dict:
        # Strictly test the integration using the SIEM endpoint for the last minute.
        # As requested, if the token is exhausted, expired, or invalid, this will strictly FAIL.
        response = requests.get(
            "https://tap-api-v2.proofpoint.com/v2/siem/all",
            auth=(self.integration.principal, self.integration.secret),
            params={"sinceSeconds": 60}
        )
        
        if response.status_code == 200:
            # We strictly enforce 200 OK. Even if there are no events in the last 60 seconds, 
            # it should return an empty list or success payload.
            return {"success": True}
        
        # If response is anything other than 200 (401 Unauthorized, 429 Too Many Requests, etc.), fail strictly.
        try:
            error_data = response.json()
            error_message = error_data.get("message") or error_data.get("error") or response.text
        except Exception:
            error_message = response.text
            
        return {"success": False, "error": f"HTTP {response.status_code}: {error_message}"}
