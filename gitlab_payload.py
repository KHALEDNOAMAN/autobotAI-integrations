import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.gitlab import GitlabIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext

code = """
import traceback

def executor(context):
    print("in execute")
    gl = context["clients"]['gitlab']    
    current_user = gl.user
    # print(current_user)
    group = gl.groups.get(84850810)    
    pj = []
    for project in group.projects.list(iterator=True):
        # print(project)
        pj.append(project.asdict())

    return pj
"""

gitlab_config_str = """
connection "gitlab" {
  plugin = "theapsgroup/gitlab"

  # The baseUrl of your GitLab Instance API (ignore if set in GITLAB_ADDR env var)
  # baseurl = "https://gitlab.company.com/api/v4"

  # Access Token for which to use for the API (ignore if set in GITLAB_TOKEN env var)
  # token = "x11x1xXxXx1xX1Xx11"
}
"""
gitlab_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "gitlab",
    "alias": "test-gitlab-integrationsv2*",
    "connection_type": "DIRECT",
    "token": os.environ["GITLAB_TOKEN"],
    "base_url": "https://gitlab.com/",
    "groups": ["gitlab", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
    "activeRegions": [],
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

def generate_gitlab_python_payload(gitlab_json=gitlab_json) -> Payload:
    integration = GitlabIntegration(**gitlab_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["gitlab"],
        "context": PayloadTaskContext(**context, **{"integration": gitlab_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

def generate_gitlab_steampipe_payload(gitlab_json=gitlab_json):
    integration = GitlabIntegration(**gitlab_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = gitlab_config_str
    gitlab_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select * from gitlab_group",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**gitlab_task_dict)]}
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    # gitlab_python_payload = generate_gitlab_python_payload()
    # for task in gitlab_python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     print(service.python_sdk_processor(task))
    pass

    # gitlab_steampipe_payload = generate_gitlab_steampipe_payload()
    # for task in gitlab_steampipe_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     print(service.execute_steampipe_task(task, job_type="query"))

