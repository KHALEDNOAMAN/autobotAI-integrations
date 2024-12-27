from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

open_search_python_code = """
# Import your modules here
import json  # noqa: F401

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):

    params = context["params"]  # noqa: F841
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["opensearch"]  # Supports only one client

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Example: Get Connection Information and Available indices
    client.info()
    
    return {
        "information": client.info(),
    }
"""

class TestClassOpensearch:
    def test_opensearch_token_with_direct_auth(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "username": get_keys["OPENSEARCH_USERNAME"],
            "password": get_keys["OPENSEARCH_PASSWORD"],
            "port": get_keys["OPENSEARCH_PORT"],
            "auth_type": "direct_auth",
        }
        integration = sample_integration_dict("opensearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "username": get_keys["OPENSEARCH_USERNAME"],
            "password": get_keys["OPENSEARCH_PASSWORD"][:-2],
            "port": get_keys["OPENSEARCH_PORT"],
            "auth_type": "direct_auth",
        }
        integration = sample_integration_dict("opensearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_opensearch_direct_auth_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "username": get_keys["OPENSEARCH_USERNAME"],
            "password": get_keys["OPENSEARCH_PASSWORD"],
            "port": int(get_keys["OPENSEARCH_PORT"]),
            "auth_type": "direct_auth",
        }
        integration = sample_integration_dict("opensearch", tokens)
        task = sample_python_task(
            integration, code=open_search_python_code, clients=["opensearch"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_opensearch_token_with_aws_config(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "opensearch_type": "aws_opensearch_service",
            "region": get_keys["AWS_REGION"],
            "port": get_keys["OPENSEARCH_PORT"],
            "auth_type": "aws_config",
        }
        integration = sample_integration_dict("opensearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"][:-2],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "region": get_keys["AWS_REGION"],
            "opensearch_type": "aws_opensearch_service",
            "port": get_keys["OPENSEARCH_PORT"],
            "auth_type": "aws_config",
        }
        integration = sample_integration_dict("opensearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_opensearch_aws_config_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "host_url": get_keys["OPENSEARCH_HOST_URL"],
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys["AWS_SESSION_TOKEN"],
            "opensearch_type": "aws_opensearch_service",
            "region": get_keys["AWS_REGION"],
            "port": get_keys["OPENSEARCH_PORT"],
            "auth_type": "aws_config",
        }
        integration = sample_integration_dict("opensearch", tokens)
        task = sample_python_task(
            integration, code=open_search_python_code, clients=["opensearch"]
        )
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)