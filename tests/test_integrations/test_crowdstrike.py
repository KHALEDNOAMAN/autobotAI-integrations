import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassCrowdstrike:
    def test_crowdstrike_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "client_cloud": get_keys["CROWDSTRIKE_CLOUD"],
            "client_id": get_keys["CROWDSTRIKE_CLIENT_ID"],
            "client_secret": get_keys["CROWDSTRIKE_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("crowdstrike", tokens)
        crowdstrike_query = "select * from crowdstrike_user"
        task = sample_steampipe_task(integration, query=crowdstrike_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "client_cloud": get_keys["CROWDSTRIKE_CLOUD"],
            "client_id": get_keys["CROWDSTRIKE_CLIENT_ID"],
            "client_secret": get_keys["CROWDSTRIKE_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "client_cloud": get_keys["CROWDSTRIKE_CLOUD"],
            "client_id": get_keys["CROWDSTRIKE_CLIENT_ID"],
            "client_secret": get_keys["CROWDSTRIKE_CLIENT_SECRET"][0:-2],
        }
        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
