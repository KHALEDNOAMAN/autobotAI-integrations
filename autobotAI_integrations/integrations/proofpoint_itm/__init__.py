import requests
from typing import Optional, Type, Union
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds
)
from autobotAI_integrations.models import IntegrationCategory

class ProofpointITMIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, exclude=True, description="Proofpoint ITM Base URL (e.g., https://tenant.itmsaas.proofpoint.com)")
    client_id: Optional[str] = Field(default=None, exclude=True, description="Proofpoint ITM API Client ID")
    client_secret: Optional[str] = Field(default=None, exclude=True, description="Proofpoint ITM API Client Secret")

    name: str = "Endpoint DLP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "DLP (Data Loss Prevention) and Insider Threat Management (ITM) integration for pulling user activity, "
        "alerts, and endpoint data protection incidents."
    )

class ProofpointITMService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ProofpointITMIntegration, dict]):
        if not isinstance(integration, ProofpointITMIntegration):
            integration = ProofpointITMIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_access_token(self) -> str:
        """
        Fetches the OAuth 2.0 Bearer token from Proofpoint ITM SaaS.
        """
        token_url = f"{self.integration.base_url.rstrip('/')}/v2/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.integration.client_id,
            "client_secret": self.integration.client_secret
        }
        
        response = requests.post(
            token_url,
            data=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token", "")
        else:
            raise Exception(f"Failed to fetch Proofpoint ITM token: {response.text}")

    def _test_integration(self) -> dict:
        """
        Strictly tests the integration by fetching an OAuth token and attempting a lightweight API call.
        """
        try:
            # 1. Test token generation
            token = self._get_access_token()
            if not token:
                return {"success": False, "error": "Token generation succeeded but access_token was missing in response."}

            # 2. Test a lightweight ITM API endpoint to verify scopes
            test_url = f"{self.integration.base_url.rstrip('/')}/v2/alerts?limit=1"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code in (200, 201):
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            return {"success": False, "error": f"Proofpoint ITM integration test failed: {str(e)}"}

    @staticmethod
    def get_forms():
        return {
            "label": "Endpoint DLP",
            "type": "form",
            "preview": True,
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "Base URL",
                    "placeholder": "Enter your ITM SaaS URL (e.g. https://<tenant>.itmsaas.proofpoint.com)",
                    "required": True,
                },
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter your Proofpoint ITM API Client ID",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Proofpoint ITM API Client Secret",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ProofpointITMIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        """
        Generates REST API credentials dynamically before the workflow triggers an action.
        """
        # Fetch a fresh token before running the REST API actions
        token = self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        return RestAPICreds(
            base_url=self.integration.base_url.rstrip("/"),
            headers=headers
        )
