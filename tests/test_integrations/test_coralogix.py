import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

coralogix_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    clients = context["clients"]
    client = clients["dataPrimeApiClient"]

    # Example to fetch logs between certain dates
    # for more information about the use of api,
    # visit: https://coralogix.com/docs/direct-query-http-api/

    data = client.run_query(**{
        "query": "source logs | limit 1000",
        "metadata": {
            "tier": "TIER_FREQUENT_SEARCH",
            "syntax": "QUERY_SYNTAX_DATAPRIME",
            "startDate": "2024-08-05T11:20:00.00Z",
            "endDate": "2024-08-07T11:30:00.00Z",
            "defaultSource": "logs",
        },
    })
    # Your logic to proccess data
    return data
"""


class TestClassCoralogix:
    def test_coralogix_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_url": get_keys["CORALOGIX_API_URL"],
            "api_key": get_keys["CORALOGIX_API_KEY"],
        }
        integration = sample_integration_dict("coralogix", tokens)
        task = sample_python_task(
            integration, code=coralogix_python_code, clients=["dataPrimeApiClient"]
        )
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_url": get_keys["CORALOGIX_API_URL"],
            "api_key": get_keys["CORALOGIX_API_KEY"],
        }
        integration = sample_integration_dict("coralogix", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]
        tokens = {
            "api_url": get_keys["CORALOGIX_API_URL"],
            "api_key": get_keys["CORALOGIX_API_KEY"][:-2]
        }
        integration = sample_integration_dict("coralogix", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
