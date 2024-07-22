import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


aws_security_lake_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.

def executor(context):
    clients = context["clients"]
    try:
        # Retrieve the integration-specific client for Security Lake
        client = clients["security_lake"]

        # Example: List data lakes
        response = client.list_data_lakes()
        data_lakes = response.get("DataLakes", [])

        if data_lakes:
            return data_lakes
        else:
            return [{"error": "No data lakes found."}]
    
    except Exception as e:
        return [{"error": str(e)}]
"""

class TestClassAwsSecurityLake:
    def test_aws_security_lake_steampipe_task(
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
        integration = sample_integration_dict("aws_security_lake", tokens)
        aws_security_lake_query = "select * from aws_security_lake_data"  
        task = sample_steampipe_task(integration, query=aws_security_lake_query)
        result = handle_task(task)
        test_result_format(result)

    def test_aws_security_lake_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_security_lake", tokens)
        task = sample_python_task(
            integration, code=aws_security_lake_python_code, clients=["security_lake"]
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
        integration = sample_integration_dict("aws_security_lake", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

      
        tokens["secret_key"] = get_keys["AWS_SECRET_ACCESS_KEY"][0:-2]  
        integration = sample_integration_dict("aws_security_lake", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]