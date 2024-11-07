from typing import Optional, Type, Union

from pydantic import Field
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
)

class CrowdSecIntegration(BaseSchema):
    token: Optional[str] = Field(default=None, description="token", exclude=True)

    name: Optional[str] = "CrowdSec"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "The CrowdSec Security Engine is an open source intrusion detection system that detects malicious behaviors and attacks by analyzing logs and requests."
    )


class CrowdSecService(BaseService):

    def __init__(self, ctx: dict, integration: Union[CrowdSecIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, CrowdSecIntegration):
            integration = CrowdSecIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False):
        try:
            response = requests.get(
                url=f"https://cti.api.crowdsec.net/v2/smoke/185.7.214.104",
                headers={"x-api-key": self.integration.token}
            )
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is Unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "CrowdSec",
            "type": "form",
            "children": [
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Your CTI API KEY",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return CrowdSecIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://cti.api.crowdsec.net/v2",
            headers={"x-api-key": self.integration.token},
        )
