from typing import Optional, Type, Union
from pydantic import Field
import requests

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds
)
from autobotAI_integrations.models import IntegrationCategory

class IPQSIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: str = "IPQS"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "IPQualityScore (IPQS) provides enterprise-grade fraud prevention and threat intelligence, "
        "including IP reputation, email validation, phone validation, and malicious URL scanning."
    )

class IPQSService(BaseService):
    def __init__(self, ctx: dict, integration: Union[IPQSIntegration, dict]):
        if not isinstance(integration, IPQSIntegration):
            integration = IPQSIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        # Test the API key using a benign IP on the IP Reputation endpoint
        # IPQS supports the IPQS-KEY header if the IP is passed as a query param.
        response = requests.get(
            "https://www.ipqualityscore.com/api/json/ip",
            headers={"IPQS-KEY": str(self.integration.api_key)},
            params={"ip": "8.8.8.8", "strictness": 0}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return {"success": True}
            else:
                message = data.get("message", "")
                if "Invalid or unauthorized key" in message:
                    return {"success": False, "error": message}
                else:
                    return {"success": True, "warning": message}
        
        return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "IPQualityScore (IPQS)",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your IPQS API Key",
                    "required": True,
                    "help_url": "https://www.ipqualityscore.com/user/settings",
                    "help_url_text": "Get API Key ↗",
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return IPQSIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        # IPQS supports passing the key via the IPQS-KEY header
        return RestAPICreds(
            base_url="https://www.ipqualityscore.com/api/json",
            headers={
                "IPQS-KEY": str(self.integration.api_key)
            }
        )

    def execute_rest_api_task(self, payload_task) -> tuple:
        if getattr(payload_task, "executable", None):
            payload_task.executable = payload_task.executable.replace(
                "{api_key}", str(self.integration.api_key)
            )
        return super().execute_rest_api_task(payload_task)
