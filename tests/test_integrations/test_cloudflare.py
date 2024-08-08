import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassCloudflare:
    def test_cloudflare_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        cloudflare_query = "select * from cloudflare_account"
        task = sample_steampipe_task(integration, query=cloudflare_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"][:-2],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_cloudflare_steampipe_task_token(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        cloudflare_query = "select * from cloudflare_account"
        task = sample_steampipe_task(integration, query=cloudflare_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active_token(self, get_keys, sample_integration_dict):
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"][:-1],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
