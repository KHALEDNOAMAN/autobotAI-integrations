import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations.integrations.servicenow import ServiceNowIntegration
from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
def executor(context):
    sn = context["clients"]["servicenow"]
    result = []
    
    # Get incidents resource
    incident = sn.resource(api_path='/table/incident')
    
    # Query incidents (limit to 10)
    response = incident.get(query={}, limit=10)
    
    # Process each incident
    for record in response.all():
        details = {
            "number": record.get("number"),
            "description": record.get("short_description"),
            "state": record.get("state"),
            "priority": record.get("priority"),
        }
        result.append({
            "id": record.get("sys_id"),
            "details": details,
        })
    
    return [{"result": result}]
"""

servicenow_config_str = """
connection "servicenow" {
  plugin = "servicenow"
    instance_url = "https://your_instance.service-now.com".
    username = "your_username"
    password = "your_password"
}
"""

servicenow_json = {
    "userId": "abhishek.rathod@autobot.live",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "servicenow",
    "alias": "test-servicenow-integrationsv2*",
    "connection_type": "DIRECT",
    "instance_url": os.environ["SERVICENOW_BASE_URL"],
    "username": os.environ["SERVICENOW_USERNAME"],
    "password": os.environ["SERVICENOW_PASSWORD"],
    "groups": ["servicenow", "shunyeka", "integrations-v2"],
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
        "bot_name": "ServiceNow Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}

def generate_servicenow_python_payload(servicenow_json=servicenow_json) -> Payload:
    integration = ServiceNowIntegration(**servicenow_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["servicenow"],
        "context": PayloadTaskContext(**context, **{"integration": servicenow_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    servicenow_payload = generate_servicenow_python_payload()
    print(handle_payload(servicenow_payload) )