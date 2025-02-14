import base64
import json
from typing import List, Optional, Type, Union,Dict

from pydantic import Field, field_validator
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    SDKClient,
    SDKCreds
)
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements
from .http_requests_client import HTTPRequestClient


class PythonHTTPRequestIntegration(BaseSchema):
    api_url: str = Field(default=None,exclude=True)
    headers_json : Dict[str,str] = Field(default=dict(),exclude=True)
    ignore_ssl : bool = False
    name: Optional[str] = "Python HTTP REST API"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "This is a simple example of an OpenAPI definition using all HTTP methods with various parameter types."
    )
    
    @field_validator("headers_json", mode="before")
    @classmethod
    def validate_scopes(cls, json_string) -> Dict[str,str]:
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            print(json_string)
            raise json.JSONDecodeError
    # @field_validator JSON




class PythonHTTPService(BaseService):
    def __init__(self, ctx: dict, integration: Union[PythonHTTPRequestIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, PythonHTTPRequestIntegration):
            integration = PythonHTTPRequestIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            params = {"integration_type":"aws_ses"}
            response = requests.get(self.integration.api_url+'/library/actions',headers=self.integration.headers_json,verify=self.integration.ignore_ssl,params=params)

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
                    "placeholder": "default: HTTP Integration",
                    "description": "Enter your domain api url",
                    "required": True,
                },
                {
                    "name": "ignore_ssl",
                    "type": "boolean",
                    "label": "Ignore SSL ",
                    "placeholder": "default: 'False'",
                    "description": "",
                    "required": False,
                },
                {
                    "name": "headers_json",
                    "type": "textarea",
                    "label": "Header KV",
                    "placeholder": r'{"Authorization": "Bearer ABC" }',
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return PythonHTTPRequestIntegration

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
            ConnectionInterfaces.PYTHON_SDK
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        
        return [
            {
                "clients": {
                    "python_http_requests": HTTPRequestClient(
                        api_url=payload_task.creds.envs.get('PYTHON_HTTP_API_URL'),
                        headers_json = json.loads(payload_task.creds.envs.get("PYTHON_HTTP_HEADERS")),
                        ignore_ssl=payload_task.creds.envs.get("PYTHON_HTTP_IGNORE_SSL"),
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
            "PYTHON_HTTP_IGNORE_SSL": self.integration.ignore_ssl
        }
        return SDKCreds(envs=creds)
