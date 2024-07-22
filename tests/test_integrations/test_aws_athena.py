import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

aws_athena_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]
    try:
        # Placeholder for retrieving the integration-specific client if needed
        client = clients["athena"]

        # User's Python code execution logic goes here
        # (Replace this comment with the your actual code)

        # Modify/Replace the below code by your own logic
        # Example:
        response = client.list_databases(CatalogName="AwsDataCatalog")
        databases = response.get("DatabaseList", [])

        if len(databases) > 0:
            return databases
        else:
            return [{
                "error": "No databases found in the specified catalog."
            }]
    except Exception as e: 
        return {
            "error": e,
            "clients": context["clients"]
        }
"""


class TestClassAws_athena:
    def test_aws_athena_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_athena", tokens)
        aws_athena_query = "select * from aws_athena_workgroup"
        task = sample_steampipe_task(integration, query=aws_athena_query)
        result = handle_task(task)
        test_result_format(result)

    def test_aws_athena_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_athena", tokens)
        task = sample_python_task(
            integration, code=aws_athena_python_code, clients=["athena"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_athena", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"][0:-2],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_athena", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
