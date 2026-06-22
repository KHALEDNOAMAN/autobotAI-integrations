from typing import Optional, Type, Union
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests ,re 
from pydantic import Field, field_validator

from autobotAI_integrations.models import IntegrationCategory, MCPCreds

class AutobotAIIntegration(BaseSchema):
    base_url: str = Field(default=None, description="base url")
    api_key: str = Field(default=None, exclude=True)
    name: Optional[str] = "AutobotAI"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "autobotAI is an advanced automation platform that enhances cloud efficiency and security through AI-based decision-making. Its visual interface simplifies workflow creation and deployment."
    )

class AutobotAIService(BaseService):
    def __init__(self, ctx: dict, integration: Union[AutobotAIIntegration, dict]):
        if not isinstance(integration, AutobotAIIntegration):
            integration = AutobotAIIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        # The default "self" integration points at the same autobotAI instance;
        # its base_url/api_key are sentinels resolved at request time by core
        # (shared.services.autobotai_self). Nothing to validate here.
        if self.integration.base_url == "self" or self.integration.api_key == "self":
            return {"success": True}
        try:
            user_endpoint =  f"{self.integration.base_url}/integrations"
            response = requests.get(
                user_endpoint,
                headers={
                    "Authorization": f"ApiKey {self.integration.api_key}"
                }
            )
            if response.status_code == 200:
                return {"success": True}
            
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed. Please check your api key",
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Error: Not Found. Invalid AutobotAI Api URL",
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
            "label": "AutobotAI",
            "type": "form",
            "children": [
                {
                    "label": "AutobotAI Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "AutobotAI Instance URL",
                            "placeholder": "https://api.instance.autobot.live",
                            "description": "Your AutobotAI API URL",
                            "required": True,
                        },
                        {
                            "name": "api_key",
                            "type": "text/password",
                            "label": "API Key",
                            "placeholder": "Enter the AutobotAI API Key",
                            "required": True,
                        }
                    ]
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return AutobotAIIntegration
    
    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.MCP_SERVER]
    
    def generate_mcp_creds(self) -> MCPCreds:
        return MCPCreds(
            headers={
                "Authorization": f"ApiKey {self.integration.api_key}",
            },
        )