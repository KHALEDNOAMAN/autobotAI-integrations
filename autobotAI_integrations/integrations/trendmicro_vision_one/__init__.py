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


class TrendMicroVisionOneIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: Optional[str] = Field(default="https://api.xdr.trendmicro.com")

    name: Optional[str] = "TrendMicro Vision One"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "TrendMicro Vision One is a comprehensive cybersecurity platform that provides extended detection and response (XDR) capabilities, threat intelligence, and security operations management."
    )


class TrendMicroVisionOneService(BaseService):

    def __init__(self, ctx: dict, integration: Union[TrendMicroVisionOneIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, TrendMicroVisionOneIntegration):
            integration = TrendMicroVisionOneIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(
                f"{self.integration.base_url}/v3.0/healthcheck/connectivity",
                headers={
                    "Authorization": f"Bearer {self.integration.api_key}",
                    "Content-Type": "application/json"
                },
            )

            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is unreachable"}

    @staticmethod
    def get_forms():
        return {
            "label": "TrendMicro Vision One",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your TrendMicro Vision One API Key",
                    "required": True,
                },
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Base URL",
                    "placeholder": "https://api.xdr.trendmicro.com",
                    "description": "TrendMicro Vision One API base URL",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return TrendMicroVisionOneIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {self.integration.api_key}",
                "Content-Type": "application/json",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "TRENDMICRO_API_KEY": self.integration.api_key,
            "TRENDMICRO_BASE_URL": self.integration.base_url,
        }
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        
        pytmv1 = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        # Initialize TrendMicro Vision One client
        client = pytmv1.init(
            name="autobotAI",
            token=payload_task.creds.envs.get("TRENDMICRO_API_KEY"),
            url=payload_task.creds.envs.get("TRENDMICRO_BASE_URL")
        )
            
        return [
            {
                "clients": {
                    "trendmicro_vision_one": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]