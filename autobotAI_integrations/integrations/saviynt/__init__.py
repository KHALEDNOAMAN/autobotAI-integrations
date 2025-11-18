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


class SaviyntIntegration(BaseSchema):
    base_url: str = Field(default=None, description="base url")
    token : str = Field(default=None, exclude=True)
    name: Optional[str] = "Saviynt"
    ignore_ssl: bool = False
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Saviynt is an identity management solution which manages user access and provides system security and compliance."
    )

    def use_dependency(self, dependency: dict):
        if dependency.get("cspName") in ["linux", "kubernetes"]:
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
        self.token = integration.token
    
    def _test_integration(self):
            try:
                if self.integration.connection_type == ConnectionTypes.AGENT:
                    return {"success": True}
                
                headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"token {self.token}",
                }

                user_endpoint = f"{self.integration.base_url}/ECMv6/request/requestHome"
                response = requests.get(user_endpoint, headers=headers,verify=not self.integration.ignore_ssl)
                if response.status_code == 200:
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": f"Authentication failed with status code: {response.status_code}",
                    }
            except requests.exceptions.SSLError:
                return {
                "success": False,
                "error": "Request failed with invalid API URl",
                }
    
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Saviynt",
            "type": "form",
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
                        {
                            "name": "token",
                            "type": "text/password",
                            "label": "Saviynt Token",
                            "placeholder": "Enter the Saviynt token",
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
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
            },
        )