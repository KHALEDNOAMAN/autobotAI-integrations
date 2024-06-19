import importlib
import os
import uuid
from typing import List, Optional
from pydantic import Field

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

from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils.logging_config import logger


class OpenAIIntegration(BaseSchema):
    api_key: str = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "A research company developing and providing access to powerful large language models."
    )

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class OpenAIService(AIBaseService):

    def __init__(self, ctx, integration: OpenAIIntegration):
        if isinstance(integration, dict):
            integration = OpenAIIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            client = OpenAI(api_key=self.integration.api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Say this is a test",
                    }
                ],
                model="gpt-3.5-turbo",
            )
            print(chat_completion)
            return {"success": True}
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
        return {
            "integration_type": "openai",
            "param_definitions": [
                {
                    "name": "prompt",
                    "type": "str",
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
            "code": """import json
import traceback
def executor(context):
    openai = context['clients']['openai']
    prompt = context['params']['prompt']
    model = context['params']['model']
    resources = json.loads(json.dumps(context['params']['resources'], default=str))
    prompts = [{
        'role': 'user',
        'content': f"For each Input dict provided, return a dict with attributes such as, 'name': str name of the resource, 'action_required': boolean that shows is the action advisable or not, 'probability_score': integer that shows the probability of the result being correct, 'confidence_score': integrer that shows the confidence in judgement, 'reason': string that mentions the reason for the judgement, 'fields_evaluated': list of fields that were evaluted for the judgement, the evaluation criterion given is {prompt}. The output should be valid parseable json, do not use any markup language at all, the returned message content should be json parsable. Wait till all data is provided before starting",
    }]
    for resource in resources:
        prompts.append({
            'role': 'user',
            'content': json.dumps(resource, default=str),
        })
    prompts.append({
        'role': 'user',
        'content': "All resources are provided, return the result for each resource in the same order.",
    })
    counter = 0
    while counter < 5:  # 4 Retries
        counter = counter + 1
        chat_completion = openai.chat.completions.create(
            messages=prompts,
            model=model,
        )
        try:
            message_content = chat_completion.choices[0].message.content
            if message_content:
                if "```json" in message_content:
                    message_content = message_content.split("```json")[1].split("```")[0]
                if len(json.loads(message_content)) == len(resources):
                    for idx, response in enumerate(json.loads(message_content)):
                        if not resources[idx].get("name") or (resources[idx].get("name") and response["name"] == resources[idx]["name"]):
                            resources[idx]["decision"] = response
                        else:
                            for resource in resources:
                                if response["name"] == resource["name"]:
                                    resource["decision"] = response
                    break
        except:
            print(type(chat_completion.choices[0].message.content), chat_completion.choices[0].message.content)
            traceback.print_exc()
    print("Completed Evaluation with ", counter, "tries.")
    return resources""",
        }

    @staticmethod
    def get_forms():
        return {
            "label": "OpenAI",
            "type": "form",
            "children": [
                {
                    "label": "API Key Integration",
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
                "clients": {"openai": openai.OpenAI(api_key=self.integration.api_key)},
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

    def prompt_executor(self, model=None, prompt="", options: dict = {}):
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
                message["temperature"] = options["max_tokens"]
            counter = 0
            while counter < 5:
                counter += 1
                try:
                    result = client.chat.completions.create(
                        messages=[message], model=model
                    )
                    if result.choices[0].message.content:
                        return result.choices[0].message.content
                except:
                    continue
            return "AI-Execution Failed to Generate Result"
        if "assistant_id" not in options:
            logger.error(
                "assistant_id is required if model is not provided, and no default assistant was defined"
            )
            raise Exception("assistant_id is required if model is not provided")

        thread_id = options.get("thread_id", None)
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id

            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt,
            )

        run_id = options.get("run_id", None)
        if not run_id:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=options.get("assistant_id"),
                extra_headers={"OpenAI-Beta": "assistants=v2"},
            )
            run_id = run.id
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status != "completed":
            return {"thread_id": thread_id, "run_id": run.id, "status": run.status}
        else:
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            new_message = messages.data[0].content[0].text.value
            return {"status": run.status, "response": new_message}
