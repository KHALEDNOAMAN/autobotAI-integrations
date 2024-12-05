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


class ElasticsearchIntegration(BaseSchema):
    base_url: str = Field(default=None, description="base url", exclude=True)
    token: Optional[str] = Field(default=None, description="token", exclude=True)

    name: Optional[str] = "Elasticsearch"
    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Elasticsearch is a distributed, open-source search and analytics engine for managing and querying large volumes of structured and unstructured data in near real-time."
    )


class ElasticsearchService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ElasticsearchIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, ElasticsearchIntegration):
            integration = ElasticsearchIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            headers = {
                "Authorization": f"ApiKey {self.integration.token}",
                "Content-Type": "application/json",
            }
            # Attempt a health check endpoint
            response = requests.get(f"{self.integration.base_url.strip('/')}", headers=headers)

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
        elasticsearch = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        client = elasticsearch.Elasticsearch(
            payload_task.creds.envs.get("ELASTICSEARCH_API_URL"),
            api_key=payload_task.creds.envs.get("ELASTICSEARCH_API_KEY"),
        )
        return [
            {
                "clients": {
                    "elasticsearch": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    @staticmethod
    def get_forms():
        return {
            "label": "Elasticsearch",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "API URL",
                    "placeholder": "API URL",
                    "required": False,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Your API KEY",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return ElasticsearchIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            # ConnectionInterfaces.REST_API
        ]

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "ELASTICSEARCH_API_URL": self.integration.base_url,
            "ELASTICSEARCH_API_KEY": self.integration.token,
        }
        return SDKCreds(envs=envs)

    # def generate_rest_api_creds(self) -> RestAPICreds:
    #     return RestAPICreds(
    #         base_url=self.integration.base_url,
    #         headers={
    #             "Authorization": f"ApiKey {self.integration.token}",
    #             "Content-Type": "application/json",
    #             "Accept": "application/json",
    #         },
    #     )
