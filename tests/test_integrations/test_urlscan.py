import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassUrlscan:
    def test_urlscan_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {"api_key": get_keys["URLSCAN_API_KEY"]}
        integration = sample_integration_dict("urlscan", tokens)
        urlscan_query = (
            "select * from urlscan_search where query = 'domain:steampipe.io'"
        )
        task = sample_steampipe_task(integration, query=urlscan_query)
        result = handle_task(task)
        test_result_format(result)
    
    # "API Quotas"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"api_key": get_keys["URLSCAN_API_KEY"]}
        integration = sample_integration_dict("urlscan", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "API Quotas":
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
    
    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("urlscan")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
    
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"api_key": get_keys["URLSCAN_API_KEY"]}
        integration = sample_integration_dict("urlscan", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"api_key": get_keys["URLSCAN_API_KEY"][0:-4]}
        integration = sample_integration_dict("urlscan", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
