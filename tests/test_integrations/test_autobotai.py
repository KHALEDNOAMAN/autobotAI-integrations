from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

class TestAutobotAI:
    
    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test CyberArk integration connection with valid credentials"""
        tokens = {
            "base_url": get_keys["AUTOBOTAI_API_URL"],
            "api_key": get_keys["AUTOBOTAI_API_KEY"],
        }
        integration = sample_integration_dict("autobotai", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()        
        assert res["success"], f"Integration connection failed: {res.get('error')}"

        tokens = {
            "base_url": get_keys["AUTOBOTAI_API_URL"],
            "api_key": get_keys["AUTOBOTAI_API_KEY"][:-2],
        }
        integration = sample_integration_dict("autobotai", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]