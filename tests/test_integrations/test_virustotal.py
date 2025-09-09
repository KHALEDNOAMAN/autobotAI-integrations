import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

virustotal_python_code = """
def executor(context):
    client = context["clients"]["virustotal"]
    import base64
    url_id = base64.urlsafe_b64encode("https://github.com".encode()).decode().strip("=")
    url = client.get_object("/urls/{}".format(url_id))
    return result 
"""


class TestClassVirustotal:
    def test_virustotal_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        api_keys = {"api_key": get_keys["VTCLI_APIKEY"]}
        integration = sample_integration_dict("virustotal", api_keys)
        task = sample_python_task(
            integration, code=virustotal_python_code, clients=["virustotal"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        api_keys = {"api_key": get_keys["VTCLI_APIKEY"]}
        integration = sample_integration_dict("virustotal", api_keys)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        api_keys = {"api_key": get_keys["VTCLI_APIKEY"][:-2]}
        integration = sample_integration_dict("virustotal", api_keys)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("virustotal")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    # "Get a URL report"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        api_keys = {"api_key": get_keys["VTCLI_APIKEY"]}
        integration = sample_integration_dict("virustotal", api_keys)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Get a URL report":
                params = action.parameters_definition
                for param in params:
                    if param.name == "id":
                        import base64
                        param.values = base64.urlsafe_b64encode("https://github.com".encode()).decode().strip("=")
                action.parameters_definition = params
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()
                    assert False
