from typing import Type, Union

import uuid
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements, PayloadTask, Param
from autobotAI_integrations.models import *
import importlib
import requests

from autobotAI_integrations.models import RestAPICreds


class OllamaIntegration(BaseSchema):
    base_url: str = Field(default="http://127.0.0.1:11434", exclude=None)
    timeout: Optional[str] = None

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class OllamaService(BaseService):
    def __init__(self, ctx: dict, integration: Union[OllamaIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, OllamaIntegration):
            integration = OllamaIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(self.integration.base_url)
            assert response.ok
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Ollama Integration",
            "type": "form",
            "children": [
                {
                    "label": "Custom API Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Host Url",
                            "description": "Your Ollama Host Api Url",
                            "required": True
                        },
                        {
                            "name": "timeout",
                            "type": "number",
                            "label": "Request Timeout",
                            "placeholder": "Request timeout (Optional)",
                            "required": False
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return OllamaIntegration

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        ollama = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        return [
            {
                "clients": {
                    "ollama": ollama.Client(host=self.integration.base_url)
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {}
        return SDKCreds(envs=creds)
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()
