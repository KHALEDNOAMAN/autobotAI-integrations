from typing import Optional, Type, Union
from pydantic import Field
import requests

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds


RECORDED_FUTURE_BASE_URL = "https://api.recordedfuture.com"


class RecordedFutureIntegration(BaseSchema):
    api_token: Optional[str] = Field(default=None, exclude=True)

    name: str = "Recorded Future"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Recorded Future delivers real-time threat intelligence covering risk lists, identity exposure, "
        "playbook alerts, detection rules, malware intelligence, fusion files, and SOAR enrichment."
    )


class RecordedFutureService(BaseService):
    def __init__(self, ctx: dict, integration: Union[RecordedFutureIntegration, dict]):
        if not isinstance(integration, RecordedFutureIntegration):
            integration = RecordedFutureIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(
                f"{RECORDED_FUTURE_BASE_URL}/v2/ip/8.8.8.8",
                params={"fields": "entity"},
                headers={
                    "X-RFToken": self.integration.api_token,
                    "Accept": "application/json",
                },
                timeout=15,
            )
            if response.status_code == 200:
                return {"success": True}
            if response.status_code in (401, 403):
                return {"success": False, "error": "API token is invalid or unauthorized."}
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code} - {response.text}",
            }
        except BaseException as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Recorded Future",
            "type": "form",
            "children": [
                {
                    "name": "api_token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter the Recorded Future API Token",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return RecordedFutureIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=RECORDED_FUTURE_BASE_URL,
            api_key=self.integration.api_token,
            headers={
                "X-RFToken": self.integration.api_token,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
