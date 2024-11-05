import base64
from enum import Enum
from typing import Dict, Optional, Type, Union

from pydantic import Field, root_validator
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
)

# Supported Auth Types
class AuthType(Enum):
    NO_AUTH = "no_auth"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"


class GenericRestAPIIntegration(BaseSchema):
    # No Auth
    api_url: str
    auth_type: Union[AuthType, str] = AuthType.NO_AUTH

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
            parameters = {}
            if self.integration.auth_type == AuthType.BEARER_TOKEN.value:
                parameters["headers"] = {"Authorization": f"Bearer {self.integration.token}"}
            elif self.integration.auth_type == AuthType.BASIC_AUTH.value:
                parameters["headers"] = {
                    "Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.username, self.integration.password).encode()).decode()}"
                }
            elif self.integration.auth_type == AuthType.API_KEY.value:
                if self.integration.api_key_in == "header":
                    parameters["headers"] = {self.integration.api_key_name: self.integration.api_key_value}
                elif self.integration.api_key_in == "query":
                    parameters["params"] = {self.integration.api_key_name: self.integration.api_key_value}
            response = requests.get(
                url=self.integration.api_url,
                **parameters
            )
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
                "error": f"Request failed with invalid API URl",
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
                    "children": [
                        {
                            "name": "api_url",
                            "type": "text",
                            "label": "API URL",
                            "placeholder": "API URL",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "Bearer Token",
                    "type": "form",
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
                    ],
                },
                {
                    "label": "Basic Auth",
                    "type": "form",
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
                    ],
                },
                {
                    "label": "API Key",
                    "type": "form",
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
        if self.integration.auth_type == AuthType.BEARER_TOKEN.value:
            return RestAPICreds(
                base_url=self.integration.api_url,
                token=self.integration.token,
                headers={"Authorization": f"Bearer {self.integration.token}"},
            )
        elif self.integration.auth_type == AuthType.BASIC_AUTH.value:
            return RestAPICreds(
                base_url=self.integration.api_url,
                headers={"Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.username, self.integration.password).encode()).decode()}"},
            )
        elif self.integration.auth_type == AuthType.API_KEY.value:
            if self.integration.api_key_in == "header":
                return RestAPICreds(
                    base_url=self.integration.api_url,
                    headers={self.integration.api_key_name: self.integration.api_key_value},
                )
            elif self.integration.api_key_in == "query":
                return RestAPICreds(
                    base_url=self.integration.api_url,
                    query_params={
                        self.integration.api_key_name: self.integration.api_key_value
                    },
                )
        else:
            return RestAPICreds(
                base_url=self.integration.api_url,
            )
