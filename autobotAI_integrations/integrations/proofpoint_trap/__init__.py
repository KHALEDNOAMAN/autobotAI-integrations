import requests
import base64
from typing import Optional, Type, Union
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds
)
from autobotAI_integrations.models import IntegrationCategory

class ProofpointTRAPIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, exclude=True, description="Proofpoint TRAP Base URL (e.g. https://trap.example.com)")
    principal: Optional[str] = Field(default=None, exclude=True, description="Proofpoint Service Principal (Client ID)")
    secret: Optional[str] = Field(default=None, exclude=True, description="Proofpoint Service Secret")

    name: str = "Proofpoint TRAP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Proofpoint Threat Response Auto-Pull (TRAP) integration for remediation actions, "
        "including pulling malicious emails and managing blocklists."
    )

class ProofpointTRAPService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ProofpointTRAPIntegration, dict]):
        if not isinstance(integration, ProofpointTRAPIntegration):
            integration = ProofpointTRAPIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        """
        Tests the integration by fetching from a generic TRAP API endpoint using Basic Auth.
        """
        try:
            # Test a lightweight TRAP endpoint
            test_url = f"{self.integration.base_url.rstrip('/')}/api/incidents"
            
            # Encode credentials for HTTP Basic Auth
            auth_string = f"{self.integration.principal}:{self.integration.secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json"
            }
            
            # Use a fast timeout for UI testing responsiveness
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code in (200, 201):
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            return {"success": False, "error": f"Proofpoint TRAP integration test failed: {str(e)}"}

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "Proofpoint TRAP",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Base URL",
                    "placeholder": "Enter your TRAP Base URL (e.g. https://trap.company.com)",
                    "required": True,
                },
                {
                    "name": "principal",
                    "type": "text",
                    "label": "Service Principal",
                    "placeholder": "Enter your Proofpoint Service Principal",
                    "required": True,
                },
                {
                    "name": "secret",
                    "type": "text/password",
                    "label": "Service Secret",
                    "placeholder": "Enter your Proofpoint Service Secret",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ProofpointTRAPIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        """
        Generates REST API credentials with dynamic HTTP Basic Auth.
        """
        auth_string = f"{self.integration.principal}:{self.integration.secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        return RestAPICreds(
            base_url=self.integration.base_url.rstrip("/"),
            headers=headers
        )
