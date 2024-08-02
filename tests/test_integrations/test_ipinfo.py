import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

class TestClassIPinfo:
    def test_ipinfo_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "token": get_keys["IPINFO_TOKEN"],
        }
        integration = sample_integration_dict("ipinfo", tokens)
        ipinfo_query = "select * from ipinfo_ip where ip = '8.8.8.8'"
        task = sample_steampipe_task(integration, query=ipinfo_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {}
        integration = sample_integration_dict("ipinfo", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "token": get_keys["IPINFO_TOKEN"],
        }
        integration = sample_integration_dict("ipinfo", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "token": get_keys["IPINFO_TOKEN"][:-2],
        }
        integration = sample_integration_dict("ipinfo", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
