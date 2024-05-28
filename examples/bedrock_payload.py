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
import json
def executor(context):
    client = context["clients"]["bedrock-runtime"]
    model_id = "meta.llama3-8b-instruct-v1:0"
    user_message = "Describe the purpose of a 'hello world' program in one line."
    prompt = f\"""
    <|begin_of_text|>
    <|start_header_id|>user<|end_header_id|>
    {user_message}
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    \"""
    request = {
        "prompt": prompt,
        # Optional inference parameters:
        "max_gen_len": 512,
        "temperature": 0.5,
        "top_p": 0.9,
    }

    # Encode and send the request.
    response = client.invoke_model(body=json.dumps(request), modelId=model_id)

    # Decode the native response body.
    model_response = json.loads(response["body"].read())
    return [model_response]
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
        "clients": ["bedrock", "bedrock-runtime"],
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
