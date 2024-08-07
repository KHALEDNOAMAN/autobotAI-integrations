from typing import List, Optional, Type, Union

from pydantic import Field
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements
from .coralogix_client import CoralogixClient


class CoralogixIntegration(BaseSchema):
    api_url: str = Field(default="https://ng-api-http.coralogix.com")
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Coralogix"
    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Coralogix is a SaaS platform that analyzes log, metric, and security data in real-time and uses machine learning to streamline delivery and maintenance processes for software providers."
    )


class CoralogixService(BaseService):

    def __init__(self, ctx: dict, integration: Union[CoralogixIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, CoralogixIntegration):
            integration = CoralogixIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.post(
                url=f"{self.integration.api_url}/api/v1/dataprime/query",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {str(self.integration.api_key)}",
                },
                json={"query": "source logs | limit 1"},
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"Request failed with status code: {response.status_code}"}
        except requests.exceptions.SSLError:
            return {
                "success": False,
                "error": f"Request failed with invalid API URl",
            }
        except BaseException as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Coralogix",
            "type": "form",
            "children": [
                {
                    "name": "api_url",
                    "type": "text/url",
                    "label":"API URL",
                    "placeholder": "Enter HOST URL",
                    "description": "Enter your domain api url, for more info: https://coralogix.com/docs/coralogix-endpoints/#data-prime",
                    "required": False
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the Coralogix API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return CoralogixIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        api_url = f"{payload_task.creds.envs.get("CORALOGIX_API_URL")}/api/v1/dataprime/query"
        return [
            {
                "clients": {
                    "dataPrimeApiClient": CoralogixClient(
                        api_url=api_url,
                        api_key=payload_task.creds.envs.get("CORALOGIX_APIKEY"),
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {
            "CORALOGIX_API_URL": str(self.integration.api_url),
            "CORALOGIX_APIKEY": str(self.integration.api_key),
        }
        return SDKCreds(envs=creds)
