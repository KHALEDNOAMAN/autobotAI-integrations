import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

datadog_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["datadog_api_client"]  # Supports only one client
    # To Learn more about usage visit: https://datadogpy.readthedocs.io/en/latest/

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Example: Get the total number of active host scrapes(for illustration purposes only)
    result = client.Hosts.totals()
    return result
"""


class TestClassDatadog:
    def test_datadog_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_url": get_keys["DATADOG_HOST"],
            "app_key": get_keys["DD_CLIENT_APP_KEY"],
            "api_key": get_keys["DD_CLIENT_API_KEY"],
        }
        integration = sample_integration_dict("datadog", tokens)
        datadog_query = "select * from datadog_user"
        task = sample_steampipe_task(integration, query=datadog_query)
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)

    def test_datadog_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_url": get_keys["DATADOG_HOST"],
            "app_key": get_keys["DD_CLIENT_APP_KEY"],
            "api_key": get_keys["DD_CLIENT_API_KEY"],
        }
        integration = sample_integration_dict("datadog", tokens)
        task = sample_python_task(
            integration, code=datadog_python_code, clients=["datadog_api_client"]
        )
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_url": get_keys["DATADOG_HOST"],
            "app_key": get_keys["DD_CLIENT_APP_KEY"],
            "api_key": get_keys["DD_CLIENT_API_KEY"],
        }
        integration = sample_integration_dict("datadog", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "api_url": get_keys["DATADOG_HOST"],
            "app_key": get_keys["DD_CLIENT_APP_KEY"],
            "api_key": get_keys["DD_CLIENT_API_KEY"][:-1],
        }
        integration = sample_integration_dict("datadog", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
    
    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("datadog")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
    
    #  "Validate API key"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "api_url": get_keys["DATADOG_HOST"],
            "app_key": get_keys["DD_CLIENT_APP_KEY"],
            "api_key": get_keys["DD_CLIENT_API_KEY"],
        }
        integration = sample_integration_dict("datadog", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Validate API key":
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                    assert False
                except Exception as e:
                    traceback.print_exc()
                    assert False
