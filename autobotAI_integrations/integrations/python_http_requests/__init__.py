import json
from typing import List, Optional, Type, Union, Dict


from urllib.parse import urlparse
from pydantic import Field, field_validator
import requests
from autobotAI_integrations import BaseService, logger
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.payload_schema import PayloadTask
from .http_requests_client import HTTPRequestClient


class PythonHTTPRequestIntegration(BaseSchema):
    api_url: str = Field(default=None, exclude=True)
    headers_json: Dict[str, str] = Field(default=dict(), exclude=True)
    healthcheck_get_api_path: Optional[str] = Field(default=None, exclude=True)
    ignore_ssl: bool = False

    name: Optional[str] = "Python HTTP REST API"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "This is a simple example of an OpenAPI definition using all HTTP methods with various parameter types."
    )

    def use_dependency(self, dependency: dict):
        if dependency.get("cspName") == "linux":
            self.connection_type = ConnectionTypes.AGENT
            self.agent_ids = dependency.get("agent_ids")
            self.dependent_integration_id = dependency.get("accountId")

    @field_validator("ignore_ssl", mode="before")
    @classmethod
    def validate_ignore_ssl(cls, ignore_ssl) -> bool:
        if isinstance(ignore_ssl, bool):
            return ignore_ssl
        elif isinstance(ignore_ssl, str):
            if ignore_ssl.lower() == "true":
                return True
            elif ignore_ssl.lower() == "false":
                return False
        raise ValueError("Invalid ignore_ssl passed !")

    @field_validator("headers_json", mode="before")
    @classmethod
    def validate_headers_json(cls, headers_json) -> Dict[str, str]:
        if isinstance(headers_json, dict):
            return headers_json
        try:
            return json.loads(headers_json)
        except json.JSONDecodeError:
            logger.error("Headers Json: %s", headers_json)
            raise json.JSONDecodeError
        except Exception:
            raise ValueError("Invalid headers passed !")

    # @field_validator JSON


class PythonHTTPService(BaseService):
    def __init__(
        self, ctx: dict, integration: Union[PythonHTTPRequestIntegration, dict]
    ):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, PythonHTTPRequestIntegration):
            integration = PythonHTTPRequestIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            if self.integration.connection_type == ConnectionTypes.AGENT:
                return {"success": True}
            urlparse(self.integration.api_url)
            if self.integration.healthcheck_get_api_path is None:  
                return {"success": True}
            test_url = self.integration.api_url.rstrip('/') + '/' + self.integration.healthcheck_get_api_path.lstrip('/')
            response = requests.get(test_url,
                headers=self.integration.headers_json,
                verify=self.integration.ignore_ssl,
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.SSLError:
            return {
                "success": False,
                "error": "Request failed with invalid API URl",
            }
        except BaseException as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    # antd - js
    @staticmethod
    def get_forms():
        return {
            "label": "Python HTTP Request",
            "type": "form",
            "children": [
                {
                    "name": "api_url",
                    "type": "text/url",
                    "label": "API URL",
                    "placeholder": "e.g., https://api.example.com",
                    "description": "Enter the base URL of your API endpoint.",
                    "required": True,
                },
                {
                    "name": "ignore_ssl",
                    "type": "select",
                    "label": "Ignore SSL",
                    "placeholder": "default: 'False'",
                    "description": "Select whether to ignore SSL certificate validation.",
                    "options": [
                        {"label": "True", "value": "True"},
                        {"label": "False", "value": "False"},
                    ],
                    "required": False,
                },
                {
                    "name": "headers_json",
                    "type": "textarea",
                    "label": "Headers (Key-Value)",
                    "placeholder": r'{"Authorization": "Bearer ABC"}',
                    "description": "Provide the request headers in JSON format.",
                    "required": True,
                },
                {
                    "name": "healthcheck_get_api_path",
                    "type": "text",
                    "label": "GET API Path for Testing",
                    "placeholder": r"/healthcheck",
                    "description": "Specify a GET API path to test the integration. If left empty, no periodic verification will be performed.",
                    "required": False,
                },
                {
                    "name": "integration_id",
                    "type": "select",
                    "integrationType": "linux",
                    "dataType": "integration",
                    "label": "Integration Id",
                    "placeholder": "Enter Integration Id",
                    "description": "Select the agent hosting OpenSearch for managed integration, or choose 'None' to establish a direct connection.",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return PythonHTTPRequestIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        return [
            {
                "clients": {
                    "python_http_requests": HTTPRequestClient(
                        api_url=payload_task.creds.envs.get("PYTHON_HTTP_API_URL"),
                        headers_json=json.loads(
                            payload_task.creds.envs.get("PYTHON_HTTP_HEADERS")
                        ),
                        ignore_ssl=payload_task.creds.envs.get(
                            "PYTHON_HTTP_IGNORE_SSL"
                        ).lower() == "true",
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {
            "PYTHON_HTTP_API_URL": self.integration.api_url,
            "PYTHON_HTTP_HEADERS": json.dumps(self.integration.headers_json),
            "PYTHON_HTTP_IGNORE_SSL": str(self.integration.ignore_ssl),
        }
        return SDKCreds(envs=creds)
