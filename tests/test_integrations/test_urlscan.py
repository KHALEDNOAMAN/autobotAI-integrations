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
