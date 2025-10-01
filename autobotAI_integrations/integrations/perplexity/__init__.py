import importlib
from typing import List, Optional, Type, Union
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory, RestAPICreds, SDKClient, SDKCreds
from autobotAI_integrations.payload_schema import PayloadTask


class PerplexityIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: str = "Perplexity"
    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "Perplexity AI is an AI-powered search engine and conversational AI platform that provides accurate, real-time answers with citations."
    )


class PerplexityService(BaseService):
    def __init__(self, ctx: dict, integration: Union[PerplexityIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, PerplexityIntegration):
            integration = PerplexityIntegration(**integration)
        super().__init__(ctx, integration)
    
    def get_integration_specific_details(self) -> dict:
        try:
            return {
                "integration_id": self.integration.accountId,
                "models": [
                    "sonar",
                    "sonar-pro",
                    "sonar-reasoning-pro",
                    "sonar-reasoning",
                    "sonar-deep-research",
                    "r1-1776",
                ],
            }
        except Exception as e:
            return {"error": "Details can not be fetched"}

    def _test_integration(self) -> dict:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {self.integration.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "user",
                        "content": "What are the major AI developments and announcements from today across the tech industry?",
                    }
                ],
            },
        )
        if response.status_code == 200:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Perplexity",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the Perplexity API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return PerplexityIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK
        ]
    
    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "PERPLEXITY_API_KEY": self.integration.api_key,
        }
        return SDKCreds(envs=envs)
    
    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        perplexity = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        return [
            {
                "clients": {
                    "perplexity": perplexity.Perplexity(
                        api_key=payload_task.creds.envs.get("PERPLEXITY_API_KEY"),
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://api.perplexity.ai",
            headers={
                "Authorization": f"Bearer {self.integration.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )