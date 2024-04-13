from autobotAI_integrations import IntegrationV2Schema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.aws import AWSIntegration
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
    ExecutionDetails,
    Caller,
)
import os, uuid

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_SESSION_TOKEN=""

aws_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "aws",
    # don't commit your keys
    "access_key": AWS_ACCESS_KEY_ID,
    "secret_key": AWS_SECRET_ACCESS_KEY,
    "session_token": AWS_SESSION_TOKEN,
    "alias": "test-aws-integrationsv2",
    "connection_type": "DIRECT",
    "groups": ["aws", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
    "activeRegions": ["us-east-1", "ap-south-1"],
}

aws_config_str = """
connection "aws" {
  plugin = "aws"

  #regions = ["ap-south-1"]

  #default_region = "us-east-1"

  #profile = "myprofile"

  #max_error_retry_attempts = 9

  #min_error_retry_delay = 25

  #ignore_error_codes = ["AccessDenied", "AccessDeniedException", "NotAuthorized", "UnauthorizedOperation", "UnrecognizedClientException", "AuthorizationError"]

  #endpoint_url = "http://localhost:4566"

  # Set to `true` to force S3 requests to use path-style addressing,
  # i.e., `http://s3.amazonaws.com/BUCKET/KEY`. By default, the S3 client
  # will use virtual hosted bucket addressing when possible (`http://BUCKET.s3.amazonaws.com/KEY`).
  #s3_force_path_style = false
}
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
    "global_variables": {"default_aws_region": "us-east-1"},
}


def generate_aws_steampipe_payload(aws_json=aws_json) -> Payload:
    aws_integration = AWSIntegration(**aws_json)
    aws_service = integration_service_factory.get_service(None, aws_integration)
    creds = aws_service.generate_steampipe_creds()
    creds.config = aws_config_str
    aws_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select * from aws_s3_bucket",
        "context": PayloadTaskContext(**context, **{"integration": aws_integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**aws_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_aws_python_payload(aws_json=aws_json):
    aws_integration = AWSIntegration(**aws_json)
    aws_service = integration_service_factory.get_service(None, aws_integration)
    creds = aws_service.generate_python_sdk_creds()
    aws_python_task = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": '\ndef executor(context):\n    clients = context[\'clients\']\n    exec_details = context[\'execution_details\']\n    resources = context[\'resources\']\n    integration_details = context[\'integration\']  ### AccountId, ProjectName, SubscriptionId etc\n    s3_client = context[\'clients\']["s3"]\n    buckets = s3_client.list_buckets()["Buckets"]\n    for bucket in buckets:\n        bucket["name"] = bucket.pop("Name")\n        bucket["id"] = bucket["name"]\n    return buckets\n',
        "clients": ["s3"],
        "params": {},
        "node_details": {"filter_resources": False},
        "context": PayloadTaskContext(**context, **{"integration": aws_integration}),
        "resources": [],
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**aws_python_task)],
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == '__main__':
    aws_steampipe_payload = generate_aws_steampipe_payload(aws_json)
    # for task in steampipe_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.execute_steampipe_task(task, job_type="query")
    #     print(output)

    aws_python_payload = generate_aws_python_payload(aws_json)
    # for task in python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.python_sdk_processor(payload_task=task)
    #     print(output)
