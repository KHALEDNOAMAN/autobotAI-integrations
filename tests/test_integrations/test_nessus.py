import pytest
from autobotAI_integrations.integrations import integration_service_factory


class TestClassNessus:
    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("nessus")
        actions = service.get_all_rest_api_actions()
        assert isinstance(actions, list)
        assert len(actions) == 4
        action_names = [a.name for a in actions]
        assert "List Scans" in action_names
        assert "Launch Scan" in action_names

    def test_generate_rest_api_creds(self, sample_integration_dict):
        tokens = {
            "url": "https://localhost:8834",
            "access_key": "dummy_access",
            "secret_key": "dummy_secret",
            "verify_ssl": False,
        }
        integration = sample_integration_dict("nessus", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://localhost:8834"
        assert "accessKey=dummy_access" in creds.headers["X-ApiKeys"]

    def test_get_details(self):
        service = integration_service_factory.get_service_cls("nessus")
        details = service.get_details()
        assert "clients" in details
        assert details["supported_executor"] == "ecs"
        assert details["compliance_supported"] is False
        assert "supported_interfaces" in details
        assert "python_code_sample" in details
        assert details.get("preview") is True

    def test_get_forms(self):
        service = integration_service_factory.get_service_cls("nessus")
        forms = service.get_forms()
        assert forms is not None
        assert forms.get("label") == "Nessus"
        assert len(forms.get("children", [])) == 4

    def test_integration_active_invalid_url(self, sample_integration_dict):
        tokens = {
            "url": "https://invalid-nonexistent-nessus-host.local:8834",
            "access_key": "dummy",
            "secret_key": "dummy",
            "verify_ssl": False,
        }
        integration = sample_integration_dict("nessus", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
        assert "Failed to connect to Nessus" in res["error"] or "error" in res["error"].lower()
