import importlib
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from pydantic import Field, field_validator

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    CLICreds,
    AIBaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)
from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils.logging_config import logger


class AzureFoundryOpenAIIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)
    azure_endpoint: str
    openai_api_version: Optional[str] = "v1"

    name: Optional[str] = "Azure Foundry OpenAI"
    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "Azure AI Foundry OpenAI integration."
    )

    @field_validator("azure_endpoint", mode='before')
    def validate_azure_endpoint(cls, value):
        if not value.startswith("https://"):
            raise ValueError("Host URL must start with 'https://'")
        return value.strip('/')



class AzureOpenAIService(AIBaseService):
    def __init__(self, ctx, integration: AzureFoundryOpenAIIntegration):
        if isinstance(integration, dict):
            integration = AzureFoundryOpenAIIntegration(**integration)

        super().__init__(ctx, integration)

    def get_openai_client(self):
        from openai import OpenAI

        return OpenAI(
            api_key=self.integration.api_key,
            base_url=f"{self.integration.azure_endpoint}/openai/{self.integration.openai_api_version}/",
        )

    def _test_integration(self):
        try:
            client = self.get_openai_client()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test!",
                    }
                ],
            )

            if response:
                return {"success": True}

            return {
                "success": False,
                "error": "Unknown response",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def get_integration_specific_details(self) -> dict:
        try:
            available_models = [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-5",
                "gpt-5-mini",
                "o3",
            ]

            return {
                "integration_id": self.integration.accountId,
                "models": available_models,
                "embedding_models": [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                ],
            }

        except Exception:
            return {
                "error": "Details can not be fetched"
            }

    @staticmethod
    def ai_prompt_python_template():
        current_directory = Path(__file__).resolve().parent

        with open(os.path.join(current_directory, "ai_evaluator_code.py")) as f:
            return {
                "integration_type": "azure_foundry_openai",
                "ai_client": "azure_openai",
                "param_definitions": [
                    {
                        "name": "prompt",
                        "type": "handlebars-text",
                        "description": "The prompt to use for the AI model",
                        "required": True,
                    },
                    {
                        "name": "model",
                        "type": "str",
                        "description": (
                            "Azure OpenAI deployment name"
                        ),
                        "required": True,
                    },
                    {
                        "name": "resources",
                        "type": "list",
                        "description": (
                            "The resources to use for the AI model"
                        ),
                        "required": True,
                    },
                ],
                "code": f.read(),
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Azure OpenAI",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "Azure OpenAI API Key",
                    "placeholder": "Enter Azure OpenAI API Key",
                    "required": True,
                },
                {
                    "name": "azure_endpoint",
                    "type": "text",
                    "label": "Azure Endpoint",
                    "placeholder": (
                        "https://<resource>.openai.azure.com/"
                    ),
                    "required": True,
                },
                {
                    "name": "openai_api_version",
                    "type": "text",
                    "label": "OpenAI API Version",
                    "placeholder": "v1",
                    "required": False,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return AzureFoundryOpenAIIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self,
        payload_task: PayloadTask,
        client_definitions: List[SDKClient],
    ) -> list:
        openai = importlib.import_module(
            client_definitions[0].import_library_names[0],
            package=None,
        )

        client = openai.OpenAI(
            api_key=self.integration.api_key,
            base_url=f"{self.integration.azure_endpoint}/openai/{self.integration.openai_api_version}/",
        )

        return [
            {
                "clients": {
                    "openai": client,
                },
                "params": self.prepare_params(
                    payload_task.params
                ),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
            "AZURE_OPENAI_ENDPOINT": (
                self.integration.azure_endpoint
            ),
            "OPENAI_API_VERSION": (
                self.integration.azure_api_version
            ),
        }

        conf_path = "~/.steampipe/config/openai.spc"

        config_str = """connection "openai" {
  plugin = "openai"
}
"""

        return SteampipeCreds(
            envs=envs,
            plugin_name="openai",
            connection_name="openai",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "api-key": self.integration.api_key,
        }

        return RestAPICreds(
            api_key=self.integration.api_key,
            headers=headers,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
            "AZURE_OPENAI_ENDPOINT": (
                self.integration.azure_endpoint
            ),
            "OPENAI_API_VERSION": (
                self.integration.azure_api_version
            ),
        }

        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass

    def get_pydantic_agent(
        self,
        model: str,
        tools,
        system_prompt: str,
        options: dict = {},
    ):
        from pydantic_ai import Agent

        model_instance = self.get_pydantic_model(model)

        return Agent(
            model_instance,
            system_prompt=system_prompt,
            tools=tools,
            **options,
        )

    def get_pydantic_model(self, model_name: str):
        from pydantic_ai.models.openai import (
            OpenAIResponsesModel,
        )
        from pydantic_ai.providers.openai import (
            OpenAIProvider,
        )

        provider = OpenAIProvider(
            api_key=self.integration.api_key,
            base_url=(
                f"{self.integration.azure_endpoint}/openai/v1/"
            ),
        )

        model = OpenAIResponsesModel(
            model_name=model_name,
            provider=provider,
        )

        return model

    # def load_llama_index_embedding_model(
    #     self,
    #     model_name: Optional[str] = None,
    #     **kwargs,
    # ):
    #     if not model_name:
    #         model_name = "text-embedding-3-small"
    #
    #     from llama_index.embeddings.azure_openai import (
    #         AzureOpenAIEmbedding,
    #     )
    #
    #     embed_model = AzureOpenAIEmbedding(
    #         api_key=self.integration.api_key,
    #         azure_endpoint=self.integration.azure_endpoint,
    #         deployment_name=model_name,
    #         model=model_name,
    #         **kwargs,
    #     )
    #
    #     return embed_model

    # def load_llama_index_llm(
    #     self,
    #     model,
    #     **kwargs,
    # ):
    #     from llama_index.llms.azure_openai import (
    #         AzureOpenAI,
    #     )
    #
    #     llm = AzureOpenAI(
    #         api_key=self.integration.api_key,
    #         azure_endpoint=self.integration.azure_endpoint,
    #         deployment_name=model,
    #         model=model,
    #         **kwargs,
    #     )
    #
    #     return llm

    def generate_llm_credentials(self):
        return {
            "api_key": self.integration.api_key,
            "azure_endpoint": (
                self.integration.azure_endpoint
            ),
        }

    def prompt_executor(
        self,
        model=None,
        prompt="",
        params=None,
        options: dict = {},
        messages: List[Dict[str, Any]] = [],
    ):
        logger.info(f"Executing prompt: {prompt}")

        client = self.get_openai_client()

        if not model:
            raise Exception("Model is Required")

        message = {
            "role": "user",
            "content": prompt,
        }

        messages.append(message)

        counter = 0

        while counter < 5:
            counter += 1

            try:
                kwargs = {
                    "messages": messages,
                    "model": model,
                }

                if "temperature" in options:
                    kwargs["temperature"] = (
                        options["temperature"]
                    )

                if "max_tokens" in options:
                    kwargs["max_tokens"] = (
                        options["max_tokens"]
                    )

                if params not in {
                    "get_code",
                    "approval",
                    "chat",
                    "params",
                    "title",
                    "message",
                }:
                    kwargs["response_format"] = {
                        "type": "json_object"
                    }

                result = (
                    client.chat.completions.create(
                        **kwargs
                    )
                )

                logger.info(
                    "result is %s",
                    result,
                )

                if result.choices[0].message.content:
                    return (
                        result.choices[0]
                        .message.content
                    )

            except Exception as e:
                logger.error(str(e))

        return "AI-Execution Failed to Generate Result"