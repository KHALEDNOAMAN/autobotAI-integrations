from typing import Type, Union

import uuid
from pydantic import Field


from autobotAI_integrations import list_of_unique_elements, PayloadTask, Param, AIBaseService
from autobotAI_integrations.models import *
import importlib
import ollama
import requests

from autobotAI_integrations.models import RestAPICreds

class OllamaIntegration(BaseSchema):
    base_url: str = Field(default="http://127.0.0.1:11434", exclude=None)
    timeout: Optional[str] = None

    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "A platform for running and integrating large language models, including compatibility with OpenAI's API."
    )


class OllamaService(AIBaseService):
    def __init__(self, ctx: dict, integration: Union[OllamaIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, OllamaIntegration):
            integration = OllamaIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            response = requests.get(self.integration.base_url)
            assert response.ok
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_integration_specific_details(self) -> dict:
        try:
            client = ollama.Client(self.integration.base_url)
            models = [model.get('model') for model in client.list()["models"]]
            return {
                "integration_id": self.integration.accountId,
                "models": models,
            }
        except Exception as e:
            return {
                "error": "Details can not be fetched"
            }

    @classmethod
    def get_details(cls):
        return {
            "python_code_sample": cls.get_code_sample(),
            "supported_interfaces": cls.supported_connection_interfaces(),
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "preview": True
        }

    @staticmethod
    def get_forms():
        return {
            "label": "Ollama Integration",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Host Url",
                    "placeholder": "Ollama Host Base Url",
                    "description": "Your Ollama Host Api Url",
                    "required": True,
                },
                {
                    "name": "timeout",
                    "type": "number",
                    "label": "Request Timeout",
                    "placeholder": "Request timeout (Optional)",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def ai_prompt_python_template():
        return {
            "integration_type": "ollama",
            "param_definitions": [
                {"name": "prompt",
                 "type": "str",
                 "description": "The prompt to use for the AI model",
                 "required": True},
                {"name": "model",
                 "type": "str",
                 "description": "The model to use for the AI model",
                 "required": True},
                {"name": "resources",
                 "type": "list",
                 "description": "The resources to use for the AI model",
                 "required": True}
            ],
            "code": """import json
def executor(context):
    ollama = context['clients']['ollama']
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
        'content': "All resources are provided, return the result for each resource in the same order in a list. DO NOT SEND ANY TEXT OTHER THAN THE RESULT JSON. SEND FULL RESULT IN THE RESPONSE.",
    })
    response = ollama.chat(
        model=model,
        messages=prompts
    )
    print(response)
    for idx, res in enumerate(json.loads(response['message']['content'])):
        resources[idx]["decision"] = res
    return resources"""}
    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return OllamaIntegration

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        ollama = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        return [
            {
                "clients": {
                    "ollama": ollama.Client(host=self.integration.base_url)
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {}
        return SDKCreds(envs=creds)

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()
