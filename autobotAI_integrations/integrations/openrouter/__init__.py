import importlib
import os
from typing import List, Optional, Dict, Any
from pydantic import Field
import requests
from pathlib import Path

from autobotAI_integrations import (
    BaseSchema,
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


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "OpenRouter"
    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "A unified API gateway that provides access to hundreds of large language models from multiple providers through a single OpenAI-compatible interface."
    )


class OpenRouterService(AIBaseService):
    def __init__(self, ctx, integration: OpenRouterIntegration):
        if isinstance(integration, dict):
            integration = OpenRouterIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            response = requests.get(
                f"{OPENROUTER_BASE_URL}/auth/key",
                headers={"Authorization": f"Bearer {self.integration.api_key}"},
            )
            if response.status_code == 200:
                return {"success": True}
            if response.status_code == 401:
                return {"success": False, "error": "API key is invalid."}
            return {
                "success": False,
                "error": f"An error occurred: {response.status_code} - {response.text}",
            }
        except BaseException as e:
            return {"success": False, "error": str(e)}

    def get_integration_specific_details(self) -> dict:
        try:
            available_models = [
                "openai/gpt-5",
                "openai/gpt-5-mini",
                "openai/gpt-4o",
                "openai/gpt-4o-mini",
                "anthropic/claude-opus-4-7",
                "anthropic/claude-sonnet-4-6",
                "anthropic/claude-haiku-4-5",
                "google/gemini-2.5-pro",
                "google/gemini-2.5-flash",
                "meta-llama/llama-3.3-70b-instruct",
                "mistralai/mistral-large",
                "deepseek/deepseek-r1",
            ]
            return {
                "integration_id": self.integration.accountId,
                "models": available_models,
            }
        except Exception:
            return {"error": "Details can not be fetched"}

    @staticmethod
    def ai_prompt_python_template():
        current_directory = Path(__file__).resolve().parent
        with open(os.path.join(current_directory, "ai_evaluator_code.py")) as f:
            return {
                "integration_type": "openrouter",
                "ai_client": "openai",
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
                        "description": "The model to use for the AI model",
                        "required": True,
                    },
                    {
                        "name": "resources",
                        "type": "list",
                        "description": "The resources to use for the AI model",
                        "required": True,
                    },
                ],
                "code": f.read(),
            }

    @staticmethod
    def get_forms():
        return {
            "label": "OpenRouter",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "OpenRouter API Key",
                    "placeholder": "Enter the OpenRouter API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return OpenRouterIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        openai = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "openai": openai.OpenAI(
                        api_key=payload_task.creds.envs.get("OPENROUTER_API_KEY"),
                        base_url=OPENROUTER_BASE_URL,
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {"Authorization": f"Bearer {self.integration.api_key}"}
        return RestAPICreds(
            base_url=OPENROUTER_BASE_URL,
            api_key=self.integration.api_key,
            headers=headers,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "OPENROUTER_API_KEY": self.integration.api_key,
            "OPENROUTER_BASE_URL": OPENROUTER_BASE_URL,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass

    def get_pydantic_agent(
        self, model: str, tools, system_prompt: str, options: dict = {}
    ):
        from pydantic_ai import Agent
        model_instance = self.get_pydantic_model(model)
        return Agent(model_instance, system_prompt=system_prompt, tools=tools, **options)

    def get_pydantic_model(self, model_name: str):
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        model = OpenAIModel(
            model_name=model_name,
            provider=OpenAIProvider(
                api_key=self.integration.api_key,
                base_url=OPENROUTER_BASE_URL,
            ),
        )
        return model

    def load_llama_index_llm(self, model, **kwargs):
        from llama_index.llms.openai_like import OpenAILike

        llm = OpenAILike(
            api_key=self.integration.api_key,
            api_base=OPENROUTER_BASE_URL,
            model=model,
            is_chat_model=True,
            **kwargs,
        )
        return llm

    def prompt_executor(
        self,
        model=None,
        prompt="",
        params=None,
        options: dict = {},
        messages: List[Dict[str, Any]] = [],
    ):
        from openai import OpenAI

        logger.info(f"Executing prompt: {prompt}")
        client = OpenAI(
            api_key=self.integration.api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        if not model:
            raise Exception("Model is Required")

        message = {
            "role": "user",
            "content": prompt,
        }
        if "temperature" in options:
            message["temperature"] = options["temperature"]
        if "max_tokens" in options:
            message["max_tokens"] = options["max_tokens"]
        counter = 0
        messages.append(message)
        while counter < 5:
            counter += 1
            try:
                kwargs = {"messages": messages, "model": model}
                if params not in {"get_code", "approval", "chat", "params", "title", "message"}:
                    kwargs["response_format"] = {"type": "json_object"}
                result = client.chat.completions.create(**kwargs)
                logger.info("result is %s", result)
                if result.choices[0].message.content:
                    return result.choices[0].message.content
            except Exception as e:
                logger.error(str(e))
        return "AI-Execution Failed to Generate Result"
