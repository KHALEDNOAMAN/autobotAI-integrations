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

# Embedding models exposed for Memory Spaces. OpenRouter requires
# provider-namespaced ids. The first entry is the default (see
# load_llama_index_embedding_model and MemorySpaceModel defaults in core).
OPENROUTER_EMBEDDING_MODELS = [
    "openai/text-embedding-3-small",
    "qwen/qwen3-embedding-8b",
    "qwen/qwen3-embedding-4b",
    "google/gemini-embedding-2",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
]


class OpenRouterIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)
    skip_test: Optional[bool] = Field(default=None, exclude=False)

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
            if self.integration.skip_test:
                return {"success": True}
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
                "deepseek/deepseek-v4-flash",
                "openrouter/owl-alpha",
                "qwen/qwen3.7-max",
                "moonshotai/kimi-k2.6",
                "minimax/minimax-m3",
                "tencent/hy3-preview",
                "deepseek/deepseek-v4-pro",
                "xiaomi/mimo-v2.5",
                "anthropic/claude-sonnet-4.6",
                "anthropic/claude-opus-4.7",
                "anthropic/claude-opus-4.8",
                "stepfun/step-3.7-flash",
                "nvidia/nemotron-3-ultra-550b-a55b:free",
                "google/gemini-3.5-flash",
                "nvidia/nemotron-3-super-120b-a12b:free",
                "openai/gpt-oss-120b",
                "z-ai/glm-5.1",
            ]
            return {
                "integration_id": self.integration.accountId,
                "models": available_models,
                "embedding_models": OPENROUTER_EMBEDDING_MODELS,
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
                },
                {
                    "name": "skip_test",
                    "type": "select",
                    "label": "Skip Test Integration",
                    "placeholder": "Skip the integration test",
                    "description": "If enabled, skips the integration test (useful when API is not accessible)",
                    "required": True,
                    "options": [
                        {"label": "No", "value": False},
                        {"label": "Yes", "value": True},
                    ],
                    "default": False,
                },
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

    def generate_llm_credentials(self):
        # OpenRouter is an OpenAI-compatible gateway, so the deep-agent runtime
        # talks to it through an OpenAI client pointed at OPENROUTER_BASE_URL.
        # NOTE: the consuming runtime (agent_core) must map provider="openrouter"
        # onto that OpenAI-compatible client using base_url for this to work end
        # to end; returning the creds here is necessary but not sufficient.
        return {
            "api_key": self.integration.api_key,
            "base_url": OPENROUTER_BASE_URL,
        }

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

    def load_llama_index_embedding_model(
        self, model_name: Optional[str] = None, **kwargs
    ):
        """
        Returns a Llama Index embedding model pointed at OpenRouter's
        OpenAI-compatible ``/embeddings`` endpoint.

        OpenRouter requires provider-namespaced model ids (e.g.
        ``openai/text-embedding-3-small``). Per the LlamaIndex maintainer's
        recommendation for OpenAI-compatible endpoints, we pass the id via
        ``model_name`` (not ``model``): ``model`` validates against a fixed
        enum and would raise on a prefixed id, while ``model_name`` sets the
        engine actually sent on the wire and ``model`` falls back to a valid
        default that only satisfies that internal validation.
        See https://github.com/run-llama/llama_index/discussions/11809
        """
        if not model_name:
            model_name = OPENROUTER_EMBEDDING_MODELS[0]
        from llama_index.embeddings.openai import OpenAIEmbedding

        embed_model = OpenAIEmbedding(
            api_key=self.integration.api_key,
            api_base=OPENROUTER_BASE_URL,
            model_name=model_name,
            **kwargs,
        )
        return embed_model

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
