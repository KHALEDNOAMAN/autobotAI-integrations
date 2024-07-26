import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassWiz:
    def test_wiz_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "url": get_keys["WIZ_URL"],
            "client_id": get_keys["WIZ_CLIENT_ID"],
            "client_secret": get_keys["WIZ_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("wiz", tokens)
        wiz_query = "select * from wiz_user"
        task = sample_steampipe_task(integration, query=wiz_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "url": get_keys["WIZ_URL"],
            "client_id": get_keys["WIZ_CLIENT_ID"],
            "client_secret": get_keys["WIZ_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("wiz", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "url": get_keys["WIZ_URL"],
            "client_id": get_keys["WIZ_CLIENT_ID"],
            "client_secret": get_keys["WIZ_CLIENT_SECRET"][0:-2]
        }
        integration = sample_integration_dict("wiz", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
