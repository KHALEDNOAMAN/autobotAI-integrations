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

class TrellixDLPIntegration(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True, description="Trellix Client ID from the Developer Portal")
    client_secret: Optional[str] = Field(default=None, exclude=True, description="Trellix Client Secret for OAuth 2.0")
    api_key: Optional[str] = Field(default=None, exclude=True, description="Trellix API Key (x-api-key) for request metering")

    name: str = "Trellix DLP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Trellix Data Loss Prevention (DLP) integration to monitor endpoints and retrieve data protection incidents."
    )

class TrellixDLPService(BaseService):
    def __init__(self, ctx: dict, integration: Union[TrellixDLPIntegration, dict]):
        if not isinstance(integration, TrellixDLPIntegration):
            integration = TrellixDLPIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_access_token(self) -> str:
        """
        Fetches the OAuth 2.0 Bearer token from Trellix IAM.
        """
        token_url = "https://iam.cloud.trellix.com/iam/v1.0/token"
        payload = {
            "grant_type": "client_credentials"
        }
        # Trellix expects the Client ID and Secret to be passed as Basic Auth for the token request.
        response = requests.post(
            token_url,
            data=payload,
            auth=(self.integration.client_id, self.integration.client_secret),
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token", "")
        else:
            raise Exception(f"Failed to fetch Trellix token: {response.text}")

    def _test_integration(self) -> dict:
        """
        Strictly tests the integration by fetching an OAuth token and attempting a lightweight API call.
        """
        try:
            # 1. Test token generation
            token = self._get_access_token()
            if not token:
                return {"success": False, "error": "Token generation succeeded but access_token was missing in response."}

            # 2. Test a lightweight DLP API endpoint to verify API key and scopes
            test_url = "https://api.manage.trellix.com/dpim/v2/incident?page[limit]=1"
            headers = {
                "Authorization": f"Bearer {token}",
                "x-api-key": str(self.integration.api_key),
                "Content-Type": "application/vnd.api+json"
            }
            
            response = requests.get(test_url, headers=headers, timeout=10)
            
            # If the credentials or scopes are strictly invalid, this will fail
            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
        except Exception as e:
            return {"success": False, "error": f"Trellix DLP integration test failed: {str(e)}"}

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "Trellix DLP",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter your Trellix Client ID",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Trellix Client Secret",
                    "required": True,
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your Trellix API Key (x-api-key)",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return TrellixDLPIntegration

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
            "x-api-key": str(self.integration.api_key),
            "Content-Type": "application/vnd.api+json"
        }
        
        return RestAPICreds(
            base_url="https://api.manage.trellix.com",
            headers=headers
        )
