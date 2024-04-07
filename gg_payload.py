import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.gitguardian import GitGuardianIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext


gitguardian_config_str = """
connection "gitguardian" {
  plugin = "francois2metz/gitguardian"

  # Create a personal access token at: https://dashboard.gitguardian.com/api
  # Scope:
  #  - incidents:read
  #  - audit_logs:read
  #  - members:read
  # token = ""
}
"""
gitguardian_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "gitguardian",
    "alias": "test-gitguardian-integrationsv2*",
    "connection_type": "DIRECT",
    "token": os.environ["GITGUARDIAN_TOKEN"],
    "groups": ["gitguardian", "shunyeka", "integrations-v2"],
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

# def generate_gitguardian_python_payload(gitguardian_json=gitguardian_json) -> Payload:
#     integration = GitguardianIntegration(**gitguardian_json)
#     service = integration_service_factory.get_service(None, integration)
#     creds = service.generate_python_sdk_creds()
#     task_dict = {
#         "task_id": uuid.uuid4().hex,
#         "creds": creds,
#         "connection_interface": ConnectionInterfaces.PYTHON_SDK,
#         "executable": code,
#         "clients": ["gitguardian"],
#         "context": PayloadTaskContext(**context, **{"integration": gitguardian_json}),
#     }
#     payload_dict = {
#         "job_id": uuid.uuid4().hex,
#         "tasks": [PayloadTask(**task_dict)]
#     }
#     payload = Payload(**payload_dict)
#     return payload

def generate_gitguardian_steampipe_payload(gitguardian_json=gitguardian_json):
    integration = GitGuardianIntegration(**gitguardian_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = gitguardian_config_str
    gitguardian_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select id, date, status from gitguardian_secret_incident;",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**gitguardian_task_dict)]}
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    # gitguardian_python_payload = generate_gitguardian_python_payload()
    # for task in gitguardian_python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     print(service.python_sdk_processor(task))


    gitguardian_steampipe_payload = generate_gitguardian_steampipe_payload()
    for task in gitguardian_steampipe_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        print(service.execute_steampipe_task(task, job_type="query"))

