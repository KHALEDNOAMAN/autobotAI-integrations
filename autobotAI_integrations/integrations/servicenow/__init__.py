from enum import Enum
import importlib
import re
from typing import List, Optional, Union

from pydantic import Field, field_validator
import requests

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds , \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient

from autobotAI_integrations.models import IntegrationCategory, MCPCreds


class ServiceNowAuthTypes(Enum):
    BASIC_AUTH = "basic_auth"

class ServiceNowIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = "ServiceNow"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "Enterprise IT Service Management platform for managing digital workflows and automating business processes."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, base_url) -> Optional[str]:
        servicenow_pattern = r"^https://[\w.-]+\.service-now\.com/?$"
        if base_url and base_url != "None":
            if re.match(servicenow_pattern, base_url):
                return base_url.strip("/")
            raise ValueError(f"Invalid ServiceNow Instance URL: {base_url}. Format: https://instance.service-now.com")
        raise ValueError("ServiceNow Instance URL is required")

class ServiceNowService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ServiceNowIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, ServiceNowIntegration):
            integration = ServiceNowIntegration(**integration)
        super().__init__(ctx, integration)
        self.base_url = integration.base_url
        self.username = integration.username
        self.password = integration.password

    def _test_integration(self):
        if self.username and self.password:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            user_endpoint = f"{self.base_url}/api/now/table/pa_dashboards"

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
                    "error": f"Error: Unexpected status code {response.status_code}. Response: {response.text}",
                    }
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "No authentication credentials provided"}

    @staticmethod
    def get_forms():
        return {
            "label": "ServiceNow",
            "type": "form",
            "children": 
                {
                    "label": "Basic Auth Integration",
                    "type": "form",
                    "formId": ServiceNowAuthTypes.BASIC_AUTH.value,
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "ServiceNow Instance URL",
                            "placeholder": "https://dev12345.service-now.com",
                            "description": "Your ServiceNow instance URL",
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
                },
        }

    @staticmethod
    def get_schema(ctx=None):
        return ServiceNowIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def build_python_exec_combinations_hook(self,payload_task:PayloadTask,client_definitions:List[SDKClient])->List:
        servicenow = importlib.import_module(client_definitions[0].import_library_names[0], package=None)

        servicenow_client = servicenow.ServiceNowClient(
        payload_task.creds.envs.get("SERVICENOW_BASE_URL"),
        (
            payload_task.creds.envs.get("SERVICENOW_USERNAME"),
            payload_task.creds.envs.get("SERVICENOW_PASSWORD")
        )
        )   

        return[
            {
            "clients": {
                "servicenow": servicenow_client,
            },
            "params":self.prepare_params(payload_task.params),
            "context":payload_task.context
            }
        ]

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
        
    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "SERVICENOW_BASE_URL": self.base_url,
            "SERVICENOW_USERNAME": self.username,
            "SERVICENOW_PASSWORD": self.password,
        }
        return SDKCreds(envs=envs)
 
    def generate_cli_creds(self) -> CLICreds:
        pass