import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

prometheus_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]
    try:
        # Placeholder for retrieving the integration-specific client if needed
        clients = context["clients"]

        # Placeholder for retrieving the integration-specific client if needed
        client = clients["prometheus_api_client"]  # Supports only one client
        result = client.all_metrics()
        return result  # Replace with your actual return logic
    except Exception as e: 
        return {
            "error": e,
            "clients": context["clients"]
        }
"""


class TestClassPrometheus:
    def test_prometheus_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {"host_url": get_keys["PROMETHEUS_URL"]}
        integration = sample_integration_dict("prometheus", tokens)
        prometheus_query = "select * from prometheus_metric where query = 'prometheus_http_requests_total'"
        task = sample_steampipe_task(integration, query=prometheus_query)
        result = handle_task(task)
        test_result_format(result)

    def test_prometheus_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"host_url": get_keys["PROMETHEUS_URL"]}
        integration = sample_integration_dict("prometheus", tokens)
        task = sample_python_task(
            integration, code=prometheus_python_code, clients=["prometheus_api_client"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"host_url": get_keys["PROMETHEUS_URL"]}
        integration = sample_integration_dict("prometheus", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"host_url": get_keys["PROMETHEUS_URL"][0:-4]}
        integration = sample_integration_dict("prometheus", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
