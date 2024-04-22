from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.azure import AzureIntegration
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
)
from autobotAI_integrations.handlers import handle_payload
import uuid, os
import dotenv

dotenv.load_dotenv()

azure_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "azure",
    "tenant_id": os.environ.get("AZURE_TENANT_ID"),
    "client_id": os.environ.get("AZURE_CLIENT_ID"),
    "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
    "client_secret": os.environ.get("AZURE_CLIENT_SECRET"),
    "alias": "test-azure-integrationsv2",
    "connection_type": "DIRECT",
    "groups": ["azure", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

azure_config_str = """
connection "azure" {
  plugin = "azure"

  ignore_error_codes = ["NoAuthenticationInformation", "InvalidAuthenticationInfo", "AccountIsDisabled", "UnauthorizedOperation", "UnrecognizedClientException", "AuthorizationError", "AuthenticationFailed", "InsufficientAccountPermissions"]
}
"""
code = """

"""
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


def generate_azure_steampipe_payload(azure_json = azure_json) -> Payload:
    azure_integration = AzureIntegration(**azure_json)
    azureservice = integration_service_factory.get_service(None, azure_integration)
    creds = azureservice.generate_steampipe_creds()
    creds.config = azure_config_str
    azure_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select * from azuread_user",
        "context": PayloadTaskContext(**context, **{"integration": azure_integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**azure_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_azure_python_payload(azure_json = azure_json):
    azure_integration = AzureIntegration(**azure_json)
    azure_service = integration_service_factory.get_service(None, azure_integration)
    creds = azure_service.generate_python_sdk_creds()
    azure_python_task = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": [],
        "node_details": {"filter_resources": False},
        "context": PayloadTaskContext(**context, **{"integration": azure_integration}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**azure_python_task)],
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == '__main__':
    azure_steampipe_payload = generate_azure_steampipe_payload(azure_json)
    for task in azure_steampipe_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        output = service.execute_steampipe_task(task)
        print(output)

    # azure_python_payload = generate_azure_python_payload(azure_json)
    # for task in azure_python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.python_sdk_processor(payload_task=task)
    #     print(output)
