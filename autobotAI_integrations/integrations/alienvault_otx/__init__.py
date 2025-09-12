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


class AlienvaultOTXIntegration(BaseSchema):
    base_url: str = Field(
        default="https://otx.alienvault.com", description="base url"
    )
    token: Optional[str] = Field(default=None, description="token", exclude=True)

    name: Optional[str] = "Alienvault OTX"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Alienvault OTX is a threat intelligence platform that provides security-related insights and data for detecting and responding to potential threats."
    )


class AlienvaultOTXService(BaseService):
    def __init__(self, ctx: dict, integration: Union[AlienvaultOTXIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AlienvaultOTXIntegration):
            integration = AlienvaultOTXIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            response = requests.get(
                url=self.integration.base_url + '/api/v1/users/me',
                headers={
                    "X-OTX-API-KEY": self.integration.token,  # Replace with your actual API key
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
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

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        OTXv2 = importlib.import_module("OTXv2", package=None)

        alienvault_client = OTXv2.OTXv2(
            payload_task.creds.envs.get("ALIENVAULT_OTX_TOKEN"),
        )
        return [
            {
                "clients": {
                    "OTXv2": alienvault_client,
                    "IndicatorTypes": OTXv2.IndicatorTypes
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    @staticmethod
    def get_forms():
        return {
            "label": "Alienvault OTX",
            "type": "form",
            "children": [
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Your API KEY",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return AlienvaultOTXIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK, ConnectionInterfaces.REST_API]

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "ALIENVAULT_OTX_TOKEN": self.integration.token,
        }
        return SDKCreds(envs=envs)

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "X-OTX-API-KEY": self.integration.token,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
