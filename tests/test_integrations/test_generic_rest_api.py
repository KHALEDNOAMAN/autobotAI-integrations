import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.generic_rest_api import GenericRestAPIIntegration


class TestClassGenericREST_API:
    def test_generic_rest_api_no_auth(
        self,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_url": "http://0.0.0.0:8000",
            "auth_type": "no_auth"
        }
        integration = sample_integration_dict("generic_rest_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {"api_url": "http://0.0.0.0:8000", "auth_type": "no_auth"}
        integration = sample_integration_dict("generic_rest_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_generic_rest_api_bearer_token(
        self,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_url": "http://0.0.0.0:8000",
            "token": "dummy_token",
            "auth_type": "bearer_token"
        }
        integration = sample_integration_dict("generic_rest_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

        tokens = {
            "api_url": "http://0.0.0.0:8000",
            "token": "dummy_token1",
            "auth_type": "bearer_token",
        }
        integration = sample_integration_dict("generic_rest_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
