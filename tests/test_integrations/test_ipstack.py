import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

class TestClassIPStack:
    def test_ipstack_steampipe_task(
        self,
        get_tokens,  
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_key": get_tokens("API_KEY") 
        } 
        integration = sample_integration_dict("ipstack", tokens)
        ipstack_query = "select * from ipstack_ip where ip = '99.84.45.75'"
        task = sample_steampipe_task(integration, query=ipstack_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_tokens, sample_integration_dict):
        tokens = get_tokens("ipstack") 
        integration = sample_integration_dict("ipstack", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

