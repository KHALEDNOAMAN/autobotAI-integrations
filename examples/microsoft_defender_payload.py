from autobotAI_integrations.integrations.microsoft_defender import MicrosoftDefenderIntegration
import os
import uuid
import dotenv

dotenv.load_dotenv()
from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    res = []
    client = context["clients"]["msgraph-defender"]
    
    return res
    
"""

microsoft_defender_config_str = """
connection "microsoft_defender" {
  plugin = "microsoft_defender"
  tenant_id = os.environ["AZURE_TENANT_ID"]
  client_id = os.environ["AZURE_CLIENT_ID"]
  client_secret = os.environ["AZURE_CLIENT_SECRET"]
}
"""

microsoft_defender_json = {
    "userId": "abhishek.rathod@autobot.live",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "microsoft_defender",
    "alias": "test-microsoft-defender-integrationsv2*",
    "connection_type": "DIRECT",
    "tenant_id": os.environ["AZURE_TENANT_ID"],
    "client_id": os.environ["AZURE_CLIENT_ID"],
    "client_secret": os.environ["AZURE_CLIENT_SECRET"],
    "groups": ["microsoft_defender", "shunyeka", "integrations-v2"],
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
        "bot_name": "Microsoft Defender Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}


def generate_microsoft_defender_python_payload(microsoft_defender_json=microsoft_defender_json) -> Payload:
    integration = MicrosoftDefenderIntegration(**microsoft_defender_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": [""],
        "context": PayloadTaskContext(**context, **{"integration": microsoft_defender_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    microsoft_defender_payload = generate_microsoft_defender_python_payload()
    print(handle_payload(microsoft_defender_payload) )