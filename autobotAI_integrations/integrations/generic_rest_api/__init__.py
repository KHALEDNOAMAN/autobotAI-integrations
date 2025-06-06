import base64
from enum import Enum
from typing import Optional, Type, Union
from urllib.parse import urlparse
from pydantic import Field, field_validator
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
)


# Supported Auth Types
class APIAuthType(str, Enum):
    NO_AUTH = "no_auth"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"


class GenericRestAPIIntegration(BaseSchema):
    # No Auth
    api_url: str
    auth_type: Union[APIAuthType, str] = APIAuthType.NO_AUTH
    healthcheck_get_api_path: Optional[str] = Field(default=None, exclude=True)
    ignore_ssl: bool = False

    # Bearer Token
    token: Optional[str] = Field(default=None, description="Bearer token", exclude=True)

    # Basic Auth
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)

    # API Key
    api_key_name: Optional[str] = Field(default=None, exclude=True)
    api_key_value: Optional[str] = Field(default=None, exclude=True)
    api_key_in: Optional[str] = Field(
        default="header", description="API Key Location (header, query, etc)"
    )

    name: Optional[str] = "Generic REST API"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "This is a simple example of an OpenAPI definition using all HTTP methods with various parameter types."
    )

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

    def use_dependency(self, dependency: dict):
        if dependency.get("cspName") in ["linux", "kubernetes"]:
            self.connection_type = ConnectionTypes.AGENT
            self.agent_ids = dependency.get("agent_ids")
            self.dependent_integration_id = dependency.get("accountId")


class GenericRestAPIService(BaseService):
    def __init__(self, ctx: dict, integration: Union[GenericRestAPIIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GenericRestAPIIntegration):
            integration = GenericRestAPIIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            urlparse(self.integration.api_url)
            if self.integration.healthcheck_get_api_path is None:  
                return {"success": True}
            parameters = {}
            if self.integration.auth_type == APIAuthType.BEARER_TOKEN.value:
                parameters["headers"] = {
                    "Authorization": f"Bearer {self.integration.token}"
                }
            elif self.integration.auth_type == APIAuthType.BASIC_AUTH.value:
                parameters["headers"] = {
                    "Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.username, self.integration.password).encode()).decode()}"
                }
            elif self.integration.auth_type == APIAuthType.API_KEY.value:
                if self.integration.api_key_in == "header":
                    parameters["headers"] = {
                        self.integration.api_key_name: self.integration.api_key_value
                    }
                elif self.integration.api_key_in == "query":
                    parameters["params"] = {
                        self.integration.api_key_name: self.integration.api_key_value
                    }
            test_url = self.integration.api_url.rstrip('/') + '/' + self.integration.healthcheck_get_api_path.lstrip('/')
            verify_ssl = not self.integration.ignore_ssl
            response = requests.get(url=test_url, **parameters, verify=verify_ssl)
            response.raise_for_status()
            if response.status_code == 200 or response.status_code == 201:
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

    @staticmethod
    def get_forms():
        # NOTE: Do not change the labels they are case sensitive to auth_type while used in frontend
        return {
            "label": "Generic REST API",
            "type": "form",
            "children": [
                {
                    "label": "No Auth",
                    "type": "form",
                    "formId": APIAuthType.NO_AUTH.value,
                    "children": [
                        {
                            "name": "api_url",
                            "type": "text",
                            "label": "API URL",
                            "placeholder": "API URL",
                            "required": True,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "integrationType": ["linux", "kubernetes"],
                            "dataType": "integration",
                            "label": "Integration Id",
                            "placeholder": "Enter Integration Id",
                            "description": "Select the agent hosting OpenSearch for managed integration, or choose 'None' to establish a direct connection.",
                            "required": False,
                        },
                        {
                            "name": "ignore_ssl",
                            "type": "select",
                            "label": "Ignore SSL",
                            "placeholder": "default: 'False'",
                            "description": "Select whether to ignore SSL certificate validation.",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "required": False,
                        },
                    ],
                },
                {
                    "label": "Bearer Token",
                    "type": "form",
                    "formId": APIAuthType.BEARER_TOKEN.value,
                    "children": [
                        {
                            "name": "api_url",
                            "type": "text",
                            "label": "API URL",
                            "placeholder": "API URL",
                            "required": True,
                        },
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Bearer Token",
                            "placeholder": "Bearer Token",
                            "required": True,
                        },
                        {
                            "name": "healthcheck_get_api_path",
                            "type": "text",
                            "label": "GET API Path for Testing",
                            "placeholder": "/healthcheck",
                            "description": "Specify a GET API path to test the integration. If left empty, no periodic verification will be performed.",
                            "required": False,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "integrationType": ["linux", "kubernetes"],
                            "dataType": "integration",
                            "label": "Integration Id",
                            "placeholder": "Enter Integration Id",
                            "description": "Select the agent hosting OpenSearch for managed integration, or choose 'None' to establish a direct connection.",
                            "required": False,
                        },
                        {
                            "name": "ignore_ssl",
                            "type": "select",
                            "label": "Ignore SSL",
                            "placeholder": "default: 'False'",
                            "description": "Select whether to ignore SSL certificate validation.",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "required": False,
                        },
                    ],
                },
                {
                    "label": "Basic Auth",
                    "type": "form",
                    "formId": APIAuthType.BASIC_AUTH.value,
                    "children": [
                        {
                            "name": "api_url",
                            "type": "text",
                            "label": "API URL",
                            "placeholder": "API URL",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "Username",
                            "placeholder": "Username",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Password",
                            "placeholder": "Password",
                            "required": True,
                        },
                        {
                            "name": "healthcheck_get_api_path",
                            "type": "text",
                            "label": "GET API Path for Testing",
                            "placeholder": "/healthcheck",
                            "description": "Specify a GET API path to test the integration. If left empty, no periodic verification will be performed.",
                            "required": False,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "integrationType": ["linux", "kubernetes"],
                            "dataType": "integration",
                            "label": "Integration Id",
                            "placeholder": "Enter Integration Id",
                            "description": "Select the agent hosting OpenSearch for managed integration, or choose 'None' to establish a direct connection.",
                            "required": False,
                        },
                        {
                            "name": "ignore_ssl",
                            "type": "select",
                            "label": "Ignore SSL",
                            "placeholder": "default: 'False'",
                            "description": "Select whether to ignore SSL certificate validation.",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "required": False,
                        },
                    ],
                },
                {
                    "label": "API Key",
                    "type": "form",
                    "formId": APIAuthType.API_KEY.value,
                    "children": [
                        {
                            "name": "api_url",
                            "type": "text",
                            "label": "API URL",
                            "placeholder": "API URL",
                            "required": True,
                        },
                        {
                            "name": "api_key_name",
                            "type": "text",
                            "label": "API Key Name",
                            "placeholder": "API Key Name",
                            "required": True,
                        },
                        {
                            "name": "api_key_value",
                            "type": "text/password",
                            "label": "API Key Value",
                            "placeholder": "API Key Value",
                            "required": True,
                        },
                        {
                            "name": "api_key_in",
                            "type": "select",
                            "label": "API Key Location",
                            "placeholder": "API Key Location",
                            "options": [
                                {"label": "Header", "value": "header"},
                                {"label": "Query", "value": "query"},
                            ],
                            "required": True,
                        },
                        {
                            "name": "healthcheck_get_api_path",
                            "type": "text",
                            "label": "GET API Path for Testing",
                            "placeholder": "/healthcheck",
                            "description": "Specify a GET API path to test the integration. If left empty, no periodic verification will be performed.",
                            "required": False,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "integrationType": ["linux", "kubernetes"],
                            "dataType": "integration",
                            "label": "Integration Id",
                            "placeholder": "Enter Integration Id",
                            "description": "Select the agent hosting OpenSearch for managed integration, or choose 'None' to establish a direct connection.",
                            "required": False,
                        },
                        {
                            "name": "ignore_ssl",
                            "type": "select",
                            "label": "Ignore SSL",
                            "placeholder": "default: 'False'",
                            "description": "Select whether to ignore SSL certificate validation.",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "required": False,
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GenericRestAPIIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        # details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        verify_ssl = not self.integration.ignore_ssl
        base_creds = {
            'base_url': self.integration.api_url,
            'verify_ssl': verify_ssl
        }
        
        if self.integration.auth_type == APIAuthType.BEARER_TOKEN.value:
            base_creds.update({
                'token': self.integration.token,
                'headers': {"Authorization": f"Bearer {self.integration.token}"}
            })
        elif self.integration.auth_type == APIAuthType.BASIC_AUTH.value:
            auth = base64.b64encode(f'{self.integration.username}:{self.integration.password}'.encode()).decode()
            base_creds['headers'] = {"Authorization": f"Basic {auth}"}
        elif self.integration.auth_type == APIAuthType.API_KEY.value:
            key_param = {self.integration.api_key_name: self.integration.api_key_value}
            if self.integration.api_key_in == "header":
                base_creds['headers'] = key_param
            elif self.integration.api_key_in == "query":
                base_creds['query_params'] = key_param
                
        return RestAPICreds(**base_creds)
