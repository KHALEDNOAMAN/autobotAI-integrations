import os
import uuid

from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.ollama import OllamaIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

base_url = "<YOUR_BASE_URL_HERE/>"

ollama_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "integrationState": "INACTIVE",
    "cspName": "ollama",
    "alias": "test-ollama-integrationsv2*",
    "connection_type": "DIRECT",
    "base_url": base_url,
    "groups": ["ollama", "shunyeka", "integrations-v2"],
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
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
def executor(context):
    client = context["clients"]["ollama"]
    client.pull('gemma:2b')
    response = client.generate(model='gemma:2b', prompt="describe life in 20 words?", stream=False)
    print(response['response'])
    return [
        {
            "result": response
        }
    ]
"""

def generate_ollama_python_payload(ollama_json=ollama_json) -> Payload:
    integration = OllamaIntegration(**ollama_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["ollama"],
        "context": PayloadTaskContext(**context, **{"integration": ollama_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    ollama_python_payload = generate_ollama_python_payload()
    handle_payload(ollama_python_payload, print_output=True)

