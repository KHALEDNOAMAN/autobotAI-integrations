from typing import Optional, Type, Union
from pydantic import Field,field_validator
from enum import Enum
import requests
import re
from autobotAI_integrations import BaseService
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
)

class SaviyntAuthTypes(Enum):
    BASIC_AUTH = "basic_auth"
    
class SaviyntIntegration(BaseSchema):
    base_url: str = Field(default=None, description="base url")
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = "Saviynt"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Saviynt is an identity management solution which manages user access and provides system security and compliance."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, base_url) -> Optional[str]:
        saviynt_pattern = r"^https://[\w.-]+\.saviyntcloud\.com/?$"
        if base_url and base_url != "None":
            if re.match(saviynt_pattern, base_url):
                return base_url.strip("/")
            raise ValueError(f"Invalid Saviynt Instance URL: {base_url}. Format: https://instance.saviyntcloud.com")
        raise ValueError("Saviynt Instance URL is required")


class SaviyntService(BaseService):
    
    def __init__(self,ctx:dict,integration:Union[SaviyntIntegration,dict]):
        if not isinstance(integration,SaviyntIntegration):
            integration=SaviyntIntegration(**integration)
        super().__init__(ctx,integration)
    
    def _test_integration(self):
        try:
            headers={
            "Content-Type": "application/json",
            }

            user_endpoint = f"{self.integration.base_url}/ECM/api/login"
            response = requests.post(user_endpoint, headers=headers,json={
                "username": self.integration.username,
                "password": self.integration.password
            })
            if response.status_code == 200:
                return {"success": True}
            elif response.status_code == 401:
                return {
                        "success": False,
                        "error": "Authentication failed. Please check your UserName and PassWord."
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Error: Not Found. Invalid Saviynt URL",
                }
            else:
                return {
                        "success": False,
                        "error": f"Authentication failed with status code: {response.status_code}",
                }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Saviynt",
            "type": "form",
            "formId": SaviyntAuthTypes.BASIC_AUTH.value,
            "children": [
                {
                    "label": "Saviynt Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Saviynt Instance URL",
                            "placeholder": "https://instance.saviyntcloud.com",
                            "description": "Your Saviynt instance URL",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "Username",
                            "placeholder": "Enter your Saviynt username",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Password",
                            "placeholder": "Enter your Saviynt password",
                            "required": True,
                        },
                    ],
                }
            ]
        }
    
    @staticmethod
    def get_schema(ctx=None):
        return SaviyntIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        headers={
            "Content-Type": "application/json",
        }
        user_endpoint = f"{self.integration.base_url}/ECM/api/login"
        login_request = requests.post(user_endpoint, headers=headers,json={
                "username": self.integration.username,
                "password": self.integration.password
        })
        data = login_request.json()
        token = data.get('access_token')
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {token}",
            }
        )