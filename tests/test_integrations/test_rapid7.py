import pytest
from autobotAI_integrations.integrations import integration_service_factory


class TestClassRapid7:
    
    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("rapid7")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_integration_active_invalid_key(self, sample_integration_dict):
        # Using an invalid api_key should return success: False from the real validate endpoint
        tokens = {"api_key": "invalid-key", "region": "us"}
        integration = sample_integration_dict("rapid7", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
        assert "status code" in res["error"] or "Unauthorized" in res["error"] or "Forbidden" in res["error"]
