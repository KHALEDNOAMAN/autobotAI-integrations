from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.aws_bedrock import AWSBedrockIntegration
from autobotAI_integrations.payload_schema import (
    Param,
    Payload,
    PayloadTask,
    PayloadTaskContext,
    ExecutionDetails,
    Caller,
)
import os, uuid
from autobotAI_integrations.handlers.payload_handler import handle_payload
from autobotAI_integrations.handlers.task_handler import handle_task

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_SESSION_TOKEN = ""

aws_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "aws_bedrock",
    "region": "ap-south-1",
    # don't commit your keys
    "access_key": AWS_ACCESS_KEY_ID,
    "secret_key": AWS_SECRET_ACCESS_KEY,
    "session_token": AWS_SESSION_TOKEN,
    "alias": "test-aws-integrationsv2",
    "connection_type": "DIRECT",
    "groups": ["aws", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
    "activeRegions": ["us-east-1", "ap-south-1"],
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
    "global_variables": {"default_aws_region": "ap-south-1"},
}
code = """
from pydantic import BaseModel, Field
from typing import List
import json


def executor(context):
    agent = context["clients"]["Agent"]
    prompt = 'generate summary'
    model =  'global.anthropic.claude-sonnet-4-6'
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

def generate_aws_python_payload(aws_json=aws_json):
    aws_integration = AWSBedrockIntegration(**aws_json)
    aws_service = integration_service_factory.get_service(None, aws_integration)
    res = aws_service.is_active()
    print(res)
    if not res["success"]:
        return
    creds = aws_service.generate_python_sdk_creds()
    param = {
        "type": "s3_buckets",
        "name": "s3_buckets",
        "values": [],
        "filter_relevant_resources": True,
    }
    aws_python_task = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["bedrock", "bedrock-runtime", "bedrock-agent-runtime", "Agent"],
        "params": [Param(**param)],
        "node_details": {"filter_resources": False},
        "context": PayloadTaskContext(**context, **{"integration": aws_integration}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**aws_python_task)],
    }
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    aws_python_payload = generate_aws_python_payload(aws_json)
    print(handle_task(aws_python_payload.tasks[0]))
    handle_payload(aws_python_payload, print_output=True)
