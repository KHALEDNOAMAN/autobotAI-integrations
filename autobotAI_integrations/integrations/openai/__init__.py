import importlib
import os
import uuid
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
    list_of_unique_elements,
)
from openai import OpenAI

from langchain_openai import ChatOpenAI

from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils.logging_config import logger


class OpenAIIntegration(BaseSchema):
    api_key: str = Field(default=None, exclude=True)

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
                }
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
            client = OpenAI(api_key=self.integration.api_key)
            models = client.models.list().data
            model_names = []
            for model in models:
                model_names.append(model.id)
            return {
                "integration_id": self.integration.accountId,
                "models": model_names,
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
    
    
    def langchain_authenticator(self, model):
        llm = ChatOpenAI(
            temperature=0,
            model_name=model,
            openai_api_key=self.integration.api_key
        )
        return llm

    def prompt_executor(self, model=None, prompt="",params=None, options: dict = {}, messages: List[Dict[str, Any]] = []):
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
                    result = client.chat.completions.create(
                        messages=messages, model=model, n=1,response_format={ "type": "json_object" }
                    )
                    print("result is ",result)
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
