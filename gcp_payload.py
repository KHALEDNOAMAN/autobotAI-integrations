from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.gcp import GCPIntegration
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext
)
from autobotAI_integrations.integration_schema import IntegrationSchema
import os, uuid
import dotenv
import json

dotenv.load_dotenv()

with open(os.environ["GCP_TOKEN_PATH"]) as f:
    gcp_creds = json.load(fp=f)

gcp_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    # Mention GC Keys
    "credentials": gcp_creds,
    "integrationState": "INACTIVE",
    "cspName": "gcp",
    "alias": "test-gcp-integrationsv2",
    "connection_type": "DIRECT",
    "groups": ["gcp", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

gcp_config_str = """
connection "gcp" {
  plugin    = "gcp"

  #project = "YOUR_PROJECT_ID"

  # `credentials` (optional) - Either the path to a JSON credential file that contains Google application credentials,
  # or the contents of a service account key file in JSON format. If `credentials` is not specified in a connection,
  # credentials will be loaded from:
  #   - The path specified in the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, if set; otherwise
  #   - The standard location (`~/.config/gcloud/application_default_credentials.json`)
  #credentials = "~/.config/gcloud/application_default_credentials.json"

  # `impersonate_service_account` (optional) - The GCP service account (string) which should be impersonated.
 
  #impersonate_service_account = "YOUR_SERVICE_ACCOUNT"

  #ignore_error_codes = ["401", "403"]
}
"""

gcp_code = """
def executor(context):
    clients = context[\'clients\']
    integration_details = context[\'integration\']
    project_client = clients["ProjectsClient"]
    project = project_client.get_project(name="projects/totemic-chalice-419613")
    result = [{"result": project}]
    return result
"""

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "GCP Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {"default_aws_region": "us-east-1"},
}


def generate_gcp_steampipe_payload(gcp_json=gcp_json) -> Payload:
    gcp_integration = GCPIntegration(**gcp_json)
    gcp_service = integration_service_factory.get_service(None, gcp_integration)
    creds = gcp_service.generate_steampipe_creds()
    creds.config = gcp_config_str
    aws_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select * from gcp_service_account",
        "context": PayloadTaskContext(**context, **{"integration": gcp_integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**aws_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_gcp_python_payload(gcp_json=gcp_json):
    gcp_integration = GCPIntegration(**gcp_json)
    gcp_service = integration_service_factory.get_service(None, gcp_integration)
    creds = gcp_service.generate_python_sdk_creds()
    
    # Add code executable for python
    gcp_python_task = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": gcp_code,
        "clients": ["ProjectsClient"],
        "params": {},
        "node_details": {"filter_resources": False},
        "context": PayloadTaskContext(**context, **{"integration": gcp_integration}),
        "resources": [],
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**gcp_python_task)],
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == '__main__':
    # gcp_steampipe_payload = generate_gcp_steampipe_payload(gcp_json)
    # print(gcp_steampipe_payload.model_dump_json(indent=2))
    # for task in gcp_steampipe_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.execute_steampipe_task(task, job_type="query")
    #     print(output)

    gcp_python_payload = generate_gcp_python_payload(gcp_json)
    for task in gcp_python_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        output = service.python_sdk_processor(payload_task=task)
        print(output)
