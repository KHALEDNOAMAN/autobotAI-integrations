import base64
import json
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


class WazuhIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, description="base url")

    username: Optional[str] = Field(default=None, description="username", exclude=True)
    password: Optional[str] = Field(default=None, description="password", exclude=True)

    name: Optional[str] = "Wazuh"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Wazuh is a free, open-source security platform that combines Security Information and Event Management (SIEM) and Extended Detection and Response (XDR) capabilities"
    )


class WazuhService(BaseService):
    def __init__(self, ctx: dict, integration: Union[WazuhIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, WazuhIntegration):
            integration = WazuhIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            response = requests.get(
                url=self.integration.base_url.strip("/")
                + "/security/user/authenticate",
                headers={
                    "Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.username, self.integration.password).encode()).decode()}",
                },
            )
            response.raise_for_status()
            if response.status_code == 200 and response.json().get("data", {}).get("token"):
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except (requests.exceptions.ConnectionError, json.decoder.JSONDecodeError):
            return {"success": False, "error": "Connection is Unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Wazuh",
            "type": "form",
            "info": "This integration uses JWT tokens for automation, generated via basic authentication at the `/security/user/authenticate` endpoint. Ensure the JWT token expiration is set to at least 900 seconds. You can adjust this using the PUT method at the `/security/config` endpoint.",
            "children": [
                {
                    "name": "base_url",
                    "type": "text",
                    "label": "API URL",
                    "placeholder": "API URL",
                    "required": True,
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Username",
                    "placeholder": "Username",
                    "required": True,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "Password",
                    "placeholder": "Password",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return WazuhIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details['preview'] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        response = requests.get(
            url=self.integration.base_url.strip("/")
            + "/security/user/authenticate?raw=true",
            headers={
                "Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.username, self.integration.password).encode()).decode()}",
            },
        )
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {str(response.json().get('data', {}).get('token'))}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
