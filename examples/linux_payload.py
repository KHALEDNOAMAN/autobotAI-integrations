import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.linux import LinuxIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
import os
def executor(context):
    # print(context)
    # os = context["clients"]["os"]
    print(os.getcwd())
    return [{"result": True}]
"""

linux_config_str = """
connection "exec" {
  plugin = "exec"

}
"""
linux_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "linux",
    "alias": "test-linux-integrationsv2*",
    "connection_type": "DIRECT",
    "groups": ["linux", "shunyeka", "integrations-v2"],
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

def generate_linux_python_payload(linux_json=linux_json) -> Payload:
    integration = LinuxIntegration(**linux_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["os"],
        "context": PayloadTaskContext(**context, **{"integration": linux_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

def generate_linux_steampipe_payload(linux_json=linux_json):
    integration = LinuxIntegration(**linux_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = linux_config_str
    linux_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select _ctx ->> 'connection_name' as host, stdout_output from exec_command where command = 'ls -la';",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**linux_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    linux_payload = generate_linux_python_payload()
    for task in linux_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        output = service.python_sdk_processor(payload_task=task)
        # print(output)
    # linux_steampipe_payload = generate_linux_steampipe_payload()

    # linux_payload.tasks.append(linux_steampipe_payload.tasks[0])

    # handle_payload(linux_payload, print_output=True)
    

