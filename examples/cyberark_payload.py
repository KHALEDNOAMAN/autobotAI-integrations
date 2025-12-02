import os
import uuid
import dotenv

dotenv.load_dotenv()
from autobotAI_integrations.integrations.cyberark import CyberArkIntegration
from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    res = []
    user = context["clients"]["ArkIdentityUsersService"]
    info = user.user_info() 
    res.append(info)

    return res
"""

cyberark_config_str = """
connection "cyberark" {
  plugin = "cyberark"
    instance_url = "https://example.id.cyberark.cloud".
    username = "your_username"
    password = "your_password"
}
"""

cyberark_json = {
    "userId": "abhishek.rathod@autobot.live",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "cyberark",
    "alias": "test-cyberark-integrationsv2*",
    "connection_type": "DIRECT",
    "instance_url": os.environ["CYBERARK_BASE_URL"],
    "username": os.environ["CYBERARK_USERNAME"],
    "password": os.environ["CYBERARK_PASSWORD"],
    "groups": ["cyberark", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2025-09-07T13:38:59.978056",
    "updatedAt": "2025-09-07T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "CyberArk Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}


def generate_cyberark_python_payload(cyberark_json=cyberark_json) -> Payload:
    integration = CyberArkIntegration(**cyberark_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": [""],
        "context": PayloadTaskContext(**context, **{"integration": cyberark_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    cyberark_payload = generate_cyberark_python_payload()
    print(handle_payload(cyberark_payload) )