from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

alienvault_python_code = """
# Import your modules here
import json  # noqa: F401

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):

    params = context["params"]  # noqa: F841
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["elasticsearch"]  # Supports only one client

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Example: Get Connection Information and Available indices
    client.info()

    indices = client.get(index="my_index", id="my_document_id")
    
    return {
        "information": client.info(),
        "indices": indices
    }
   
"""


class TestClassAlienvault:
    def test_alienvault_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "base_url": get_keys["ELASTICSEARCH_BASE_URL"],
            "token": get_keys["ELASTICSEARCH_TOKEN"],
        }
        integration = sample_integration_dict("elasticsearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "base_url": get_keys["ELASTICSEARCH_BASE_URL"],
            "token": get_keys["ELASTICSEARCH_TOKEN"][:-3]
        }
        integration = sample_integration_dict("elasticsearch", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_alienvault_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "base_url": get_keys["ELASTICSEARCH_BASE_URL"],
            "token": get_keys["ELASTICSEARCH_TOKEN"],
        }
        integration = sample_integration_dict("elasticsearch", tokens)
        task = sample_python_task(
            integration, code=alienvault_python_code, clients=["elasticsearch"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("elasticsearch")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) < 0
