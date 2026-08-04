import pytest
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.rapid7 import Rapid7ConsoleV3Client, Rapid7Integration


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
        with pytest.raises(Exception):
            integration_service_factory.get_service(None, sample_integration_dict("rapid7", tokens))

    def test_empty_or_whitespace_api_key(self, sample_integration_dict):
        # Empty string should raise validation error
        with pytest.raises(Exception):
            integration_service_factory.get_service(None, sample_integration_dict("rapid7", {"api_key": "", "region": "us"}))

        # Whitespace-only string should raise validation error
        with pytest.raises(Exception):
            integration_service_factory.get_service(None, sample_integration_dict("rapid7", {"api_key": "   \t  ", "region": "us"}))

        # Whitespace surrounding valid key should be stripped
        service = integration_service_factory.get_service(None, sample_integration_dict("rapid7", {"api_key": "  valid-key  ", "region": "us"}))
        assert service.integration.api_key == "valid-key"

    def test_rest_api_creds(self, sample_integration_dict):
        tokens = {
            "api_key": "test-api-key",
            "region": "us",
            "console_url": "https://console.example.com:3780/",
            "username": "admin",
            "password": "password",
        }
        integration = sample_integration_dict("rapid7", tokens)
        service = integration_service_factory.get_service(None, integration)
        rest_creds = service.generate_rest_api_creds()
        assert rest_creds.headers == {"X-Api-Key": "test-api-key"}

    def test_console_client_get_asset_vulnerabilities(self, monkeypatch):
        called = {}

        def mock_get(url, headers=None, auth=None, params=None, timeout=None):
            called["url"] = url
            called["headers"] = headers
            called["auth"] = auth
            called["params"] = params
            called["timeout"] = timeout

            class MockResponse:
                status_code = 200

                def json(self):
                    return {"resources": []}

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)
        client = Rapid7ConsoleV3Client(
            console_url="https://console.example.com:3780",
            username="admin",
            password="password",
        )
        res = client.get_asset_vulnerabilities(asset_id=123, page=1, size=50)
        assert res.status_code == 200
        assert called["url"] == "https://console.example.com:3780/api/3/assets/123/vulnerabilities"
        assert called["auth"] == ("admin", "password")
        assert called["params"] == {"page": 1, "size": 50}






