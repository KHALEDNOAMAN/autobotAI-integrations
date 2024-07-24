import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

splunk_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]
    # Placeholder for retrieving the integration-specific client if needed
    client = clients["splunk"]  # Supports only one client

    # Example: Code to search for events (for illustration purposes only)
    search_query = "search index=main | head 10"
    result = client.search(search_query)
    return [result] # Replace with your actual return logic
"""

class TestClassSplunk:
    def test_splunk_steampipe_task(self, get_keys, sample_integration_dict, sample_steampipe_task, test_result_format):
        tokens = {
            "username": get_keys["SPLUNK_USERNAME"],
            "password": get_keys["SPLUNK_PASSWORD"],
            "host_url": get_keys["SPLUNK_URL"],
        }
        integration = sample_integration_dict("splunk", tokens)
        splunk_query = "select * from splunk_user"
        task = sample_steampipe_task(integration, query=splunk_query)
        result = handle_task(task)
        test_result_format(result)

    def test_splunk_python_task(self, get_keys, sample_integration_dict, sample_python_task, test_result_format):
        tokens = {
            "username": get_keys["SPLUNK_USERNAME"],
            "password": get_keys["SPLUNK_PASSWORD"],
            "host_url": get_keys["SPLUNK_URL"],
        }
        integration = sample_integration_dict("splunk", tokens)
        task = sample_python_task(integration, code=splunk_python_code, clients=["splunk"])
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "username": get_keys["SPLUNK_USERNAME"],
            "password": get_keys["SPLUNK_PASSWORD"],
            "host_url": get_keys["SPLUNK_URL"],
        }
        integration = sample_integration_dict("splunk", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "username": get_keys["SPLUNK_USERNAME"],
            "password": get_keys["SPLUNK_PASSWORD"][:-2],
            "host_url": get_keys["SPLUNK_URL"],
        }
        integration = sample_integration_dict("splunk", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
