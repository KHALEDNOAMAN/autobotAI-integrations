import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassWhois:
    def test_whois_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {}
        integration = sample_integration_dict("whois", tokens)
        whois_query = "select * from whois_domain where domain = 'steampipe.io'"
        task = sample_steampipe_task(integration, query=whois_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {}
        integration = sample_integration_dict("whois", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
