from email.quoprimime import header_check
import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
)
from autobotAI_integrations.handlers import handle_payload
from autobotAI_integrations.integrations.python_http_requests import PythonHTTPRequestIntegration , PythonHTTPService

code = r"""
import traceback

def executor(context):
    print("in execute")
    try:
        client = context["clients"]["python_http_requests"]
        # method: str, endpoint: str, headers: dict = dict()
        url = client.request("GET","",{"public" : "abc"})
        print(url)
    except Exception as e:
        print(traceback.format_exc())
    return {"success": True}
"""

virustotal_json = {
    "userId": "jayesh.thatte@shunyeka.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "cspName": "python_http_requests",
    "alias": "test-python-http-requests",
    "api_url" : "https://tempshun.free.beeceptor.com",
    "headers_json" : {
        "Private" : "1"
    }
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
    integration = PythonHTTPRequestIntegration(**virustotal_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["python_http_requests"],
        "context": PayloadTaskContext(**context, **{"integration": virustotal_json}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**task_dict)]}
    payload = Payload(**payload_dict)
    return payload



if __name__ == "__main__":
    virustotal_python_payload = generate_virustotal_python_payload()
    handle_payload(virustotal_python_payload, print_output=True)
