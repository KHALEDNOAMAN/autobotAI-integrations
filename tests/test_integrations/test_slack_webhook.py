import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassSlack:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "webhook": get_keys["SLACK_WEBHOOK_URL"],
        }
        integration = sample_integration_dict("slack", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]
        tokens = {
            "webhook": get_keys["SLACK_WEBHOOK_URL"][:-2],
        }
        integration = sample_integration_dict("slack", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
