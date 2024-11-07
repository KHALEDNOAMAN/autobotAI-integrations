import importlib
from typing import List, Optional, Type, Union

from pydantic import Field
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.payload_schema import PayloadTask

class EmailRepIntegration(BaseSchema):
    # Bearer Token
    token: Optional[str] = Field(default=None, description="Bearer token", exclude=True)

    name: Optional[str] = "EmailRep"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "EmailRep is a system of crawlers, scanners, and enrichment services that collect data on email addresses, domains, and internet personas."
    )


class EmailRepService(BaseService):

    def __init__(self, ctx: dict, integration: Union[EmailRepIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, EmailRepIntegration):
            integration = EmailRepIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False) -> dict:
        try:
            response = requests.get(
                url= "https://emailrep.io/bsheffield432@gmail.com",
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {self.integration.token}",
                },
            )
            response.raise_for_status()
            if response.status_code == 200 or response.status_code == 201:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except BaseException as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    @staticmethod
    def get_forms():
        # NOTE: Do not change the labels they are case sensitive to auth_type while used in frontend
        return {
            "label": "Generic REST API",
            "type": "form",
            "children": [
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the EmailRep API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return EmailRepIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        emailRep = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "emailrep": emailRep(
                        payload_task.creds.envs["EMAILREP_KEY"]
                    ),
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {"EMAILREP_KEY": self.integration.token}
        return SDKCreds(envs=envs)

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://emailrep.io",
            token=self.integration.token,
            headers={"Authorization": f"Bearer {self.integration.token}"},
        )
