import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.openai import OpenAIIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

openai_config_str = """
connection "openai" {
  plugin = "openai"
}
"""
openai_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "openai",
    "alias": "test-openai-integrationsv2*",
    "connection_type": "DIRECT",
    "api_key": os.environ["OPENAI_API_KEY"],
    "groups": ["openai", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "AWS Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}
code = """
from pydantic import BaseModel, Field
from typing import List
import json


def executor(context):
    agent = context["clients"]["Agent"]
    prompt = 'generate summary'
    model =  'gpt-5.2'
    resources = 'this is resource list'

    class ResourceEvaluation(BaseModel):
        name: str = Field(..., description="Matches unique resource 'name' field")
        action_required: bool = Field(..., description="Whether action is required")
        probability_score: int = Field(..., ge=1, le=100, description="Probability score between 1 and 100")
        confidence_score: int = Field(..., ge=0, le=100, description="Confidence score between 0 and 100")
        reason: str = Field(..., description="Explanation for the scores")
        fields_evaluated: List[str] = Field(..., description="List of fields that were evaluated")


    system_prompt = f\"\"\"You are an AI evaluator that returns decision-making JSON data only.

Given the prompt and resource list, evaluate each resource based on the following field descriptions:

1. **name**: The unique name of the resource being evaluated. It should match exactly with the resource 'name' field value.

2. **action_required**: A Boolean indicating whether action is advisable for the resource. Determine this based on `probability_score` and `confidence_score`. Return `true` if action is recommended; otherwise, return `false`.

3. **probability_score**: An integer (1-100) representing the likelihood of a specific outcome occurring. Higher scores suggest automation or action; lower scores suggest manual intervention or no action.

4. **confidence_score**: An integer (0-100) reflecting the confidence in the evaluation's accuracy. Lower scores imply that more assumptions were needed to reach the result.

5. **reason**: A textual explanation justifying the `action_required` value, based on the `probability_score` and `confidence_score`.

6. **fields_evaluated**: A list of the field names considered in determining the above values.

Your response must be a JSON array with one object per resource, strictly following this schema:
{ResourceEvaluation.model_json_schema()}

Rules:
- Return only a JSON array, structured for direct parsing using `json.loads(response)` in Python.
- No extra text, symbols, or markdown.
- Each object must contain all required fields.\"\"\"

    user_prompt = f\"\"\"
    System Instructions: {system_prompt}
    Resources: {resources}
    Prompt: {prompt}

    Response: \"\"\"

    agent_instance = agent(model)

    # Execute agent
    result = agent_instance.run_sync(
        f"{system_prompt}\\n\\n{user_prompt}"
    )

    return [result.output]
"""

# steampipe_cmd = """
# select
#   completion
# from
#   openai_completion
# where
#   settings = '{
#     "model": "gpt-3.5-turbo",
#     "max_tokens": 60,
#     "temperature": 0.7,
#     "top_p": 1.0,
#     "frequency_penalty": 0.0,
#     "presence_penalty": 1
#   }'
#   and prompt = 'A neutron star is the collapsed core of a massive supergiant star,
# which had a total mass of between 10 and 25 solar masses, possibly more if the
# star was especially metal-rich.[1] Neutron stars are the smallest and densest
# stellar objects, excluding black holes and hypothetical white holes, quark
# stars, and strange stars.[2] Neutron stars have a radius on the order of 10
# kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from
# the supernova explosion of a massive star, combined with gravitational
# collapse, that compresses the core past white dwarf star density to that of
# atomic nuclei.

# TL;DR

# ';
# """
def generate_openai_python_payload(openai_json=openai_json) -> Payload:
    integration = OpenAIIntegration(**openai_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["openai"],
        "context": PayloadTaskContext(**context, **{"integration": openai_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

def generate_openai_steampipe_payload(openai_json=openai_json):
    integration = OpenAIIntegration(**openai_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = openai_config_str
    openai_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select id, created_at, object from openai_model",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**openai_task_dict)]}
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    openai_python_payload = generate_openai_python_payload()
    handle_payload(openai_python_payload, print_output=True)
    openai_steampipe_payload = generate_openai_steampipe_payload()
    handle_payload(openai_steampipe_payload, print_output=True)
