import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassGrafana:
    def test_grafana_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "host_url": get_keys["GRAFANA_URL"],
            "auth_key": get_keys["GRAFANA_AUTH"],
        }
        integration = sample_integration_dict("grafana", tokens)
        grafana_query = "select * from grafana_org"
        task = sample_steampipe_task(integration, query=grafana_query)
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "host_url": get_keys["GRAFANA_URL"],
            "auth_key": get_keys["GRAFANA_AUTH"],
        }
        integration = sample_integration_dict("grafana", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "host_url": get_keys["GRAFANA_URL"],
            "auth_key": get_keys["GRAFANA_AUTH"][:-3],
        }
        integration = sample_integration_dict("grafana", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
