import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.github import GithubIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    gh = context["clients"]["github"]
    result = []
    for repo in gh.get_user().get_repos():
        details = {
            "name": repo.name,
            "url": repo.url,
            "stars_count": repo.stargazers_count,
        }
        result.append({
            "id": repo.id,
            "details": details,
        })
    return [{"result": result}]
"""

github_config_str = """
connection "github" {
  plugin = "github"

  # The GitHub personal access token to authenticate to the GitHub APIs, e.g., `ghp_3b99b12218f63bcd702ad90d345975ef6c62f7d8`.
  # Please see https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token for more information.
  # Can also be set with the GITHUB_TOKEN environment variable.
  # token = "ghp_J1jzniKzVbFJNB34cJPwFPCmKeFakeToken"

  # GitHub Enterprise requires a base_url to be configured to your installation location.
  # Can also be set with the GITHUB_BASE_URL environment variable.
  # base_url = "https://github.example.com"
}
"""
github_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "github",
    "alias": "test-github-integrationsv2*",
    "connection_type": "DIRECT",
    "token": os.environ["GITHUB_TOKEN"],
    "groups": ["github", "shunyeka", "integrations-v2"],
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

def generate_github_python_payload(github_json=github_json) -> Payload:
    integration = GithubIntegration(**github_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["github"],
        "context": PayloadTaskContext(**context, **{"integration": github_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

def generate_github_steampipe_payload(github_json=github_json):
    integration = GithubIntegration(**github_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = github_config_str
    github_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select id, name, url, stargazer_count from github_my_repository",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**github_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    github_payload = generate_github_python_payload()
    github_steampipe_payload = generate_github_steampipe_payload()

    # github_payload.tasks.append(github_steampipe_payload.tasks[0])

    print(handle_payload(github_payload))
    

