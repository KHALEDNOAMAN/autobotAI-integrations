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
import json
def executor(context):
    client = context["clients"]["openai"]
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
        ]
    )

    print(completion.choices[0].message)
    return [
        {
            "result": completion.choices[0].message
        }
    ]
"""
steampipe_cmd = """
select
  completion
from
  openai_completion
where
  settings = '{
    "model": "gpt-3.5-turbo",
    "max_tokens": 60,
    "temperature": 0.7,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 1
  }'
  and prompt = 'A neutron star is the collapsed core of a massive supergiant star,
which had a total mass of between 10 and 25 solar masses, possibly more if the
star was especially metal-rich.[1] Neutron stars are the smallest and densest
stellar objects, excluding black holes and hypothetical white holes, quark
stars, and strange stars.[2] Neutron stars have a radius on the order of 10
kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from
the supernova explosion of a massive star, combined with gravitational
collapse, that compresses the core past white dwarf star density to that of
atomic nuclei.

TL;DR

';
"""
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
