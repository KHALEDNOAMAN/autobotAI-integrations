import os
import uuid


from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.abuseipdb import AbuseIPDBIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
)
from autobotAI_integrations.handlers import handle_payload


abuseipdb_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "abuseipdb",
    "api_key": "",
    "alias": "test-abuseipdb-integrations2*",
    "connection_type": "DIRECT",
    "groups": ["abuseipdb", "shunyeka", "integrations-v2"],
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

def generate_abuseipdb_steampipe_payload(abuseipdb_json=abuseipdb_json):
    integration = AbuseIPDBIntegration(**abuseipdb_json)
    service = integration_service_factory.get_service(None, integration)
    print(service.is_active())
    creds = service.generate_steampipe_creds()
    linux_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select ip_address, abuse_confidence_score, last_reported_at from abuseipdb_check_ip where ip_address = '76.76.21.21';",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**linux_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    abuseipdb_steampipe_payload = generate_abuseipdb_steampipe_payload()
    handle_payload(abuseipdb_steampipe_payload, print_output=True)
    


