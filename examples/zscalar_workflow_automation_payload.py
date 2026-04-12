import os
import uuid
import dotenv

from autobotAI_integrations.integrations.zscaler_workflow_automation import ZscalerWorkflowAutomationIntegration

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.linux import LinuxIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext, PayloadCommonContext
from autobotAI_integrations.handlers import handle_payload

code = """
# Import your modules here
import json


def executor(context):

    params = context["params"]
    clients = context["clients"]

    # Zscaler client (Legacy ZWA)
    client = clients["zscaler"]

    # Default parameters (aligned with your original config)
    test_body = params.get(
        "test_body",
        json.dumps({
            "fields": [
                {"name": "severity", "value": ["HIGH"]}
            ],
            "time_range": {"startTime": "2025-03-03T18:04:52.074Z", "endTime": "2026-04-09T18:04:52.074Z"}
        })
    )

    result = []

    # Ensure body is a dict
    if isinstance(test_body, str):
        body = json.loads(test_body)
    else:
        body = test_body

    # Execute SDK method
    # Reference: dlp_incidents.search_dlp_incidents
    response, status_code, err = client.zwa.dlp_incidents.dlp_incident_search(
        **body
    )
    print(response, status_code, err, body)

    if err:
        raise Exception(err)
    else:
        result.append({
            "status_code": status_code,
            "response": response
        })

    # Always return a list
    return result
"""

linux_config_str = """
connection "exec" {
  plugin = "exec"

}
"""
zscalar_workflow_automation_json = {
    "userId": "vishalshandilya2121@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "zscaler_workflow_automation",
    "alias": "test-zscaler_workflow_automation-integrations",
    "connection_type": "DIRECT",
    "groups": ["zscalar", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
    "key_id": "",
    "key_secret": ""
}

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "Zscalar Workflow Automation Integrations Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}


def generate_zscalar_workflow_automation_python_payload(zscalar_workflow_automation_json=zscalar_workflow_automation_json) -> Payload:
    integration = ZscalerWorkflowAutomationIntegration(**zscalar_workflow_automation_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["zscaler"],
        "context": PayloadTaskContext(**context, **{"integration": zscalar_workflow_automation_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)],
        "common_context": PayloadCommonContext(**context)
    }
    payload = Payload(**payload_dict)
    return payload


# def generate_linux_steampipe_payload(linux_json=linux_json):
#     integration = LinuxIntegration(**linux_json)
#     service = integration_service_factory.get_service(None, integration)
#     creds = service.generate_steampipe_creds()
#     creds.config = linux_config_str
#     linux_task_dict = {
#         "task_id": uuid.uuid4().hex,
#         "creds": creds,
#         "connection_interface": ConnectionInterfaces.STEAMPIPE,
#         "executable": "select _ctx ->> 'connection_name' as host, stdout_output from exec_command where command = 'ls -la';",
#         "context": PayloadTaskContext(**context, **{"integration": integration}),
#     }
#     payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**linux_task_dict)]}
#     payload = Payload(**payload_dict)
#     return payload


if __name__ == "__main__":
    zscalar_workflow_automation_payload = generate_zscalar_workflow_automation_python_payload()
    for task in zscalar_workflow_automation_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        output = service.python_sdk_processor(payload_task=task)
        print(output)
    # linux_steampipe_payload = generate_linux_steampipe_payload()

    # linux_payload.tasks.append(linux_steampipe_payload.tasks[0])

    # handle_payload(linux_payload, print_output=True)


