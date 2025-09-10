import importlib
import os
from typing import List, Optional, Dict, Any
from pydantic import Field
import requests
from pathlib import Path

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


class OpenAIIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "OpenAI"
    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "A research company developing and providing access to powerful large language models."
    )


class OpenAIService(AIBaseService):
    def __init__(self, ctx, integration: OpenAIIntegration):
        if isinstance(integration, dict):
            integration = OpenAIIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.integration.api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Say this is a test!"}],
                    "temperature": 0.7,
                },
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
            # TODO: USE API
            from openai import OpenAI
            client = OpenAI(api_key=self.integration.api_key)
            
            models_list = client.models.list().data
            
            tool_calling_models = [
                model.id for model in models_list
                # Only including text based tool calling models
                if any(k in model.id for k in ["gpt", "o1", "o2", "o3", "o4"])
                # Removing old and embedding models
                and not any(x in model.id for x in ["instruct", "embedding"])
            ]
            
            tool_calling_models.sort()
            
            return {
                "integration_id": self.integration.accountId,
                "models": tool_calling_models,
                "embedding_models": [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                    "text-embedding-ada-002",
                ]
            }
        except Exception as e:
            return {"error": "Details can not be fetched"}

    @staticmethod
    def ai_prompt_python_template():
        current_directory = Path(__file__).resolve().parent
        with open(os.path.join(current_directory, "ai_evaluator_code.py")) as f:
            return {
                "integration_type": "openai",
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
            "label": "OpenAI",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "OpenAI api_key",
                    "placeholder": "Enter the OpenAI API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema():
        return OpenAIIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
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
                        api_key=payload_task.creds.envs.get("OPENAI_API_KEY")
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
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
        headers = {"Authorization": f"Bearer {self.integration.api_key}"}
        return RestAPICreds(api_key=self.integration.api_key, headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "OPENAI_API_KEY": self.integration.api_key,
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass

    def get_pydantic_agent(
        self, model: str, tools, system_prompt: str, options: dict = {}
    ):
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        from pydantic_ai import Agent
        model = OpenAIModel(
            model_name=model,
            provider=OpenAIProvider(api_key=self.integration.api_key),
        )
        return Agent(model, system_prompt=system_prompt, tools=tools, **options)

    def langchain_authenticator(self, model):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            temperature=0, model_name=model, openai_api_key=self.integration.api_key
        )
        return llm
    
    def load_llama_index_embedding_model(self, model_name: Optional[str] = None, **kwargs):
        """
        Returns Llama Index Embedding model object and model dimensions as tuple
        """
        if not model_name:
            model_name = "text-embedding-3-small"
        from llama_index.embeddings.openai import OpenAIEmbedding

        embed_model = OpenAIEmbedding(
            api_key=self.integration.api_key, model=model_name, **kwargs
        )

        # embeddings = embed_model.get_text_embedding(
        #     "Open AI new Embeddings models is great."
        # )

        # dimensions = len(embeddings)

        # return embed_model, dimensions
        return embed_model

    
    def load_llama_index_llm(self, model, **kwargs):
        from llama_index.llms.openai import OpenAI
        
        llm = OpenAI(api_key=self.integration.api_key, model=model, **kwargs)
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
        client = OpenAI(api_key=self.integration.api_key)
        if model:
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
                    if params != "get_code" and params != "approval" and params!="chat" and params!="params":
                        kwargs["response_format"] = {"type": "json_object"}
                    result = client.chat.completions.create(**kwargs)
                    logger.info("result is %s", result)
                    if result.choices[0].message.content:
                        return result.choices[0].message.content
                except:
                    continue
            return "AI-Execution Failed to Generate Result"
        else:
            raise Exception("Model is Required")
        # if "assistant_id" not in options:
        #     logger.error(
        #         "assistant_id is required if model is not provided, and no default assistant was defined"
        #     )
        #     raise Exception("assistant_id is required if model is not provided")

        # thread_id = options.get("thread_id", None)
        # if not thread_id:
        #     thread = client.beta.threads.create()
        #     thread_id = thread.id

        #     message = client.beta.threads.messages.create(
        #         thread_id=thread_id,
        #         role="user",
        #         content=prompt,
        #     )

        # run_id = options.get("run_id", None)
        # if not run_id:
        #     run = client.beta.threads.runs.create(
        #         thread_id=thread_id,
        #         assistant_id=options.get("assistant_id"),
        #         extra_headers={"OpenAI-Beta": "assistants=v2"},
        #     )
        #     run_id = run.id
        # print("run is ",run)
        # print("run status is ",run.status)
        # while run.status!='completed':

        #     run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        # # if run.status != "completed":
        # #     return {"thread_id": thread_id, "run_id": run.id, "status": run.status}

        # print("run status is after ",run.status)
        # messages = client.beta.threads.messages.list(thread_id=thread_id)
        # print("message is ",message)
        # new_message = messages.data[0].content[0].text.value

        # print("new message os ",new_message)
        # return {"status": run.status, "response": new_message}
