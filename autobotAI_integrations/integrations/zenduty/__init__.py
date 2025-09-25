import importlib
from typing import Optional, Type, Union, List
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds,
    SDKCreds,
    PayloadTask,
    SDKClient,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory


class ZendutyIntegration(BaseSchema):
    api_token: Optional[str] = Field(default=None, exclude=True)

    name: str = "Zenduty"
    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "Zenduty is an incident management platform that helps teams respond to critical issues faster with intelligent alerting, escalations, and on-call scheduling."
    )


class ZendutyService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ZendutyIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, ZendutyIntegration):
            integration = ZendutyIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(
                "https://www.zenduty.com/api/account/members/",
                headers={
                    "Authorization": f"Token {self.integration.api_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            print(response.content)
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is unreachable"}

    @staticmethod
    def get_forms():
        return {
            "label": "Zenduty",
            "type": "form",
            "children": [
                {
                    "name": "api_token",
                    "type": "text/password",
                    "label": "API Token",
                    "placeholder": "Enter the Zenduty API Token",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ZendutyIntegration
    
    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://wwww.zenduty.com",
            headers={
                "Authorization": f"Token {self.integration.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "ZENDUTY_API_TOKEN": self.integration.api_token,
        }
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        zenduty = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        
        api_client = zenduty.ApiClient(payload_task.creds.envs.get("ZENDUTY_API_TOKEN"))
        
        return [
            {
                "clients": {
                    "zenduty": zenduty,
                    "api_client": api_client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]