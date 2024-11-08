import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

snyk_python_code = """

def executor(context):
    snyk_client = context['clients']['snyk']
    orgs = snyk_client.get('/orgs').json().get('data')
    return orgs
"""

class TestClassSnyk:
    def test_snyk_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "api_key": get_keys["SNYK_API_KEY"],
        }
        integration = sample_integration_dict("snyk", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "api_key": get_keys["SNYK_API_KEY"][:-2],
        }
        integration = sample_integration_dict("snyk", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_snyk_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_key": get_keys["SNYK_API_KEY"],
        }
        integration = sample_integration_dict("snyk", tokens)
        task = sample_python_task(integration, code=snyk_python_code, clients=["snyk"])
        result = handle_task(task)
        test_result_format(result)

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls('snyk')
        actions = service.get_all_rest_api_actions()
        for action in actions:
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0
