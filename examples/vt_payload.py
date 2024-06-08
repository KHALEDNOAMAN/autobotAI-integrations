import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.virustotal import VirusTotalIntegration
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
    try:
        client = context["clients"]["virustotal"]
        import base64

        url_id = base64.urlsafe_b64encode("https://github.com".encode()).decode().strip("=")
        url = client.get_object("/urls/{}".format(url_id))
        print(url)
    except Exception as e:
        print(traceback.format_exc())
    client.close()
    return {"success": True, **url.last_analysis_stats}
"""

virustotal_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "virustotal",
    "alias": "test-virustotal-integrations2*",
    "connection_type": "DIRECT",
    "api_key": os.environ["VTCLI_APIKEY"],
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


def generate_virustotal_python_payload(virustotal_json=virustotal_json) -> Payload:
    integration = VirusTotalIntegration(**virustotal_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["virustotal"],
        "context": PayloadTaskContext(**context, **{"integration": virustotal_json}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_virustotal_steampipe_payload(virustotal_json=virustotal_json):
    integration = VirusTotalIntegration(**virustotal_json)
    service = integration_service_factory.get_service(None, integration)
    print(service.is_active())
    creds = service.generate_steampipe_creds()
    virustotal_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select * from virustotal_url where url='https://github.com'",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**virustotal_task_dict)],
    }
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    virustotal_python_payload = generate_virustotal_python_payload()
    handle_payload(virustotal_python_payload, print_output=True)

    virustotal_steampipe_payload = generate_virustotal_steampipe_payload()
    handle_payload(virustotal_steampipe_payload, print_output=True)
