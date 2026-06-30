import pytest
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.rapid7 import Rapid7ConsoleV3Client


class TestClassRapid7:
    
    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("rapid7")
        actions = service.get_all_rest_api_actions()
        action_names = set()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            action_names.add(action.name)
        assert len(actions) > 0
        assert "Get Health Status" in action_names
        assert "List Integration Assets" in action_names


    def test_integration_active_invalid_key(self, sample_integration_dict):
        # Using an invalid api_key should return success: False from the real validate endpoint
        tokens = {"api_key": "invalid-key", "region": "us"}
        integration = sample_integration_dict("rapid7", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
        assert "status code" in res["error"] or "Unauthorized" in res["error"] or "Forbidden" in res["error"]

    def test_empty_credentials(self, sample_integration_dict):
        tokens = {"region": "us"}
        integration = sample_integration_dict("rapid7", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
        assert "No credentials configured" in res["error"]

    def test_console_v3_client_generation(self, sample_integration_dict):
        tokens = {
            "api_key": "test-key",
            "region": "us",
            "console_url": "https://console.example.com:3780/",
            "username": "admin",
            "password": "password",
        }
        integration = sample_integration_dict("rapid7", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert creds.envs["RAPID7_CONSOLE_URL"] == "https://console.example.com:3780"
        assert creds.envs["RAPID7_CONSOLE_USERNAME"] == "admin"
        client = Rapid7ConsoleV3Client(console_url="https://console.example.com:3780/", username="admin", password="password")
        assert client.console_url == "https://console.example.com:3780"
        assert client._auth() == ("admin", "password")


