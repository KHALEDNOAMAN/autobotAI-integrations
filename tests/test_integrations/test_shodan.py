import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
shodan_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]
    try:
        # Placeholder for retrieving the integration-specific client if needed
        client = clients["shodan"]  # Supports only one client

        # Example: Code to get Host count (for illustration purposes only)
        result = client.count(query="port:22", facets="org,os")
        return [result] # Replace with your actual return logic
    except Exception as e: 
        return {
            "error": e,
            "clients": context["clients"]
        }
"""

class TestClassShodan:
    def test_shodan_steampipe_task(self, get_keys, sample_integration_dict, sample_steampipe_task, test_result_format):
        tokens = {"api_key": get_keys["SHODAN_API_KEY"]}
        integration = sample_integration_dict("shodan", tokens)
        shodan_query = "select * from shodan_api_info"
        task = sample_steampipe_task(integration, query=shodan_query)
        result = handle_task(task)
        test_result_format(result)

    def test_shodan_python_task(self, get_keys, sample_integration_dict, sample_python_task, test_result_format):
        tokens = {"api_key": get_keys["SHODAN_API_KEY"]}
        integration = sample_integration_dict("shodan", tokens)
        task = sample_python_task(integration, code=shodan_python_code, clients=["shodan"])
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"api_key": get_keys["SHODAN_API_KEY"]}
        integration = sample_integration_dict("shodan", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"api_key": get_keys["SHODAN_API_KEY"][0: -4]}
        integration = sample_integration_dict("shodan", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
