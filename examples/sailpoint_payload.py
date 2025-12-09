import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations.integrations.sailpoint import SailPointIndentityNowIntegration
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    cli = context["clients"]["sailpoint"]

    tenant_api = TenantApi(cli).get_tenant()
    
    result = tenant_api.model_dump()
    
    return [{"result": result}]
"""

sailpoint_config_str = """
connection "sailpoint" {
  plugin = "sailpoint"
    username = "your_username"
    password = "your_password"
    tenantname = "your_tenantname"
    tenantdomain = "your_tenantdomain" 

}
"""

sailpoint_json = {
    "userId": "abhishek.rathod@autobot.live",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "sailpoint",
    "alias": "test-sailpoint-integrationsv2*",
    "connection_type": "DIRECT",
    "tenantname": os.environ["SAILPOINT_TENANTNAME"],
    "tenantdomain": os.environ["SAILPOINT_TENANTDOMAIN"],
    "username": os.environ["SAILPOINT_CLIENTID"],
    "password": os.environ["SAILPOINT_CLIENT_SECRET"],
    "groups": ["sailpoint", "shunyeka", "integrations-v2"],
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
        "bot_name": "SailPoint Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}

def generate_sailpoint_python_payload(sailpoint_json=sailpoint_json) -> Payload:
    integration = SailPointIndentityNowIntegration(**sailpoint_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["sailpoint"],
        "context": PayloadTaskContext(**context, **{"integration": sailpoint_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    sailpoint_payload = generate_sailpoint_python_payload()
    print(handle_payload(sailpoint_payload))