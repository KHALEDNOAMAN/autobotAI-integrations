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

class SaviyntauthTypes(Enum):
    BASIC_AUTH = "basic_auth"

class SaviyntIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None, description="base url")
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
            raise ValueError(f"Invalid ServiceNow Instance URL: {base_url}. Format: https://instance.saviyntcloud.com")
        raise ValueError("Saviynt Instance URL is required")


class SaviyntService(BaseService):
    
    def __init__(self,ctx:dict,integration:Union[SaviyntIntegration,dict]):
        if not isinstance(integration,SaviyntIntegration):
            integration=SaviyntIntegration(**integration)
        super().__init__(ctx,integration)
        self.base_url = integration.base_url
        self.username = integration.username
        self.password = integration.password
    
    def _test_integration(self):
        if self.username and self.password:
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            user_endpoint = f"{self.base_url}/ECMv6/request/requestHome"
            
            try:
                response = requests.get(
                user_endpoint,
                auth=(self.username, self.password),
                headers=headers,
                )
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {
                        "success": False,
                        "error": f"Authentication failed with status code: {response.status_code}",
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Saviynt",
            "type": "form",
            "children": [
                {
                    "label": "Basic Auth Integration",
                    "type": "form",
                    "formId": SaviyntauthTypes.BASIC_AUTH.value,
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "Saviynt Instance URL",
                            "placeholder": "https://company.saviyntcloud.com",
                            "description": "Your Saviynt instance URL",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "Username",
                            "placeholder": "Enter your ServiceNow username",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Password",
                            "placeholder": "Enter your ServiceNow password",
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
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.username and self.password:
            return RestAPICreds(
                base_url=self.base_url,
                headers=headers,
                auth=(self.username, self.password)
            )