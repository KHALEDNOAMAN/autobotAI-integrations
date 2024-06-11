import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.jira import JiraIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
)
from autobotAI_integrations.handlers import handle_payload

code = """
import traceback

def executor(context):
    print("in execute")
    jira = context["clients"]['jira']    
    try:
        results = []
        projects = jira.projects()
        for project in projects:
            results.append({
                "name": project.name,
                "key": project.key
            })
    except JiraApiError as e:
        print(f"Got an error: {e.response['error']}")
        return {
            "success": False
        }
    else:
        return results
"""

jira_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "jira",
    "alias": "test-jira-integrationsv2*",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "username": os.environ['JIRA_USER'],
    "base_url":  os.environ['JIRA_URL'],
    "token": os.environ['JIRA_TOKEN'],
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


def generate_jira_python_payload(jira_json=jira_json) -> Payload:
    integration = JiraIntegration(**jira_json)
    service = integration_service_factory.get_service(None, integration)
    print(service.is_active())
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["jira"],
        "context": PayloadTaskContext(**context, **{"integration": jira_json}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_jira_steampipe_payload(jira_json=jira_json):
    integration = JiraIntegration(**jira_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    jira_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select name, id, key from jira_project;",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**jira_task_dict)],
    }
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    jira_python_payload = generate_jira_python_payload()
    handle_payload(jira_python_payload, print_output=True)

    jira_steampipe_payload = generate_jira_steampipe_payload()
    handle_payload(jira_steampipe_payload, print_output=True)
