import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassNewrelic:
    def test_newrelic_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_key": get_keys["NEWRELIC_API_KEY"],
            "region": get_keys["NEWRELIC_REGION"]
        }
        integration = sample_integration_dict("newrelic", tokens)
        newrelic_query = "select * from newrelic_account"
        task = sample_steampipe_task(integration, query=newrelic_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_key": get_keys["NEWRELIC_API_KEY"],
            "region": get_keys["NEWRELIC_REGION"],
        }
        integration = sample_integration_dict("newrelic", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "api_key": get_keys["NEWRELIC_API_KEY"][0:-3],
            "region": get_keys["NEWRELIC_REGION"],
        }
        integration = sample_integration_dict("newrelic", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
