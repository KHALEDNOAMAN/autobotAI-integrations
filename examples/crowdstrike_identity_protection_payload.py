import os
import uuid
import dotenv

dotenv.load_dotenv()
from autobotAI_integrations.integrations.crowdstrike_identity_protection import CrowdstrikeIdentityProtectionIntegration
from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    res = []
    client = context["clients"]["identity_protection"]

    return res
"""

crowdstrike_identity_protection_config_str = """
connection "crowdstrike_identity_protection" {
  plugin = "crowdstrike_identity_protection"
  client_id = os.environ["FALCON_CLIENT_ID"]
  client_secret = os.environ["FALCON_CLIENT_SECRET"]
  client_cloud = os.environ["FALCON_CLOUD"]
}
"""

crowdstrike_identity_protection_json = {
    "userId": "abhishek.rathod@autobot.live",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "crowdstrike_identity_protection",
    "alias": "test-crowdstrike-identity-protection-integrationsv2*",
    "connection_type": "DIRECT",
    "client_id": os.environ["FALCON_CLIENT_ID"],
    "client_secret": os.environ["FALCON_CLIENT_SECRET"],
    "client_cloud": os.environ.get("FALCON_CLOUD", "us-2"),
    "groups": ["crowdstrike_identity_protection", "shunyeka", "integrations-v2"],
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
        "bot_name": "CrowdStrike Identity Protection Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}


def generate_crowdstrike_identity_protection_python_payload(crowdstrike_identity_protection_json=crowdstrike_identity_protection_json) -> Payload:
    integration = CrowdstrikeIdentityProtectionIntegration(**crowdstrike_identity_protection_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": [""],
        "context": PayloadTaskContext(**context, **{"integration": crowdstrike_identity_protection_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    crowdstrike_identity_protection_payload = generate_crowdstrike_identity_protection_python_payload()
    print(handle_payload(crowdstrike_identity_protection_payload))
