import importlib
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
    RestAPICreds
)
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements


class SnykIntegration(BaseSchema):
    api_url: str = Field(default="https://api.snyk.io/rest")
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Snyk"
    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Snyk is a developer security platform that helps identify and fix vulnerabilities in code, open-source libraries, containers, and infrastructure as code throughout the software development lifecycle."
    )

class SnykService(BaseService):

    def __init__(self, ctx: dict, integration: Union[SnykIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, SnykIntegration):
            integration = SnykIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # Snyk API request
            response = requests.get(
                url=f"{self.integration.api_url.strip('/')}/self?version=2024-06-10",
                headers={
                    "Content-Type": "application/vnd.api+json",
                    "Authorization": f"token {self.integration.api_key}"
                }
            )

            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False, 
                    "error": f"Request failed with status code: {response.status_code}, message: {response.text}"
                }

        except requests.exceptions.SSLError:
            return {
                "success": False,
                "error": "Request failed due to an SSL error (possibly an invalid API URL)"
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Snyk",
            "type": "form",
            "children": [
                {
                    "name": "api_url",
                    "type": "select",
                    "label": "API URL",
                    "placeholder": "Select the Snyk API URL",
                    "options":  [
                        {"label": "SNYK-US-01", "value": "https://api.snyk.io/rest"},
                        {"label": "SNYK-US-02", "value": "https://api.us.snyk.io/rest"},
                        {"label": "SNYK-EU-01", "value": "https://api.eu.snyk.io/rest"},
                        {"label": "SNYK-AU-01", "value": "https://api.au.snyk.io/rest"}
                    ],
                    "description": "Enter api url, for more info: https://docs.snyk.io/snyk-api/rest-api/about-the-rest-api#api-urls",
                    "required": True,
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the Snyk API Key",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return SnykIntegration

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
        api_url = f"{payload_task.creds.envs.get('SNYK_API_URL')}"
        snyk = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        return [
            {
                "clients": {
                    "snyk": snyk.SnykClient(
                        token=payload_task.creds.envs.get("SNYK_APIKEY"),
                        url=api_url,
                        version="2024-06-10",
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {
            "SNYK_API_URL": str(self.integration.api_url),
            "SNYK_APIKEY": str(self.integration.api_key),
        }
        return SDKCreds(envs=creds)

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.api_url,
            token=self.integration.api_key,
            headers={"Authorization": f"token {self.integration.api_key}"},
            query_params={"version": "2024-06-10"},
        )
