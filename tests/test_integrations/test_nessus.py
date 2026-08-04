import pytest
import requests
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.nessus.code_sample import executor


class TestClassNessus:
    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("nessus")
        actions = service.get_all_rest_api_actions()
        assert isinstance(actions, list)
        assert len(actions) == 18
        action_names = [a.name for a in actions]
        assert "List Scans" in action_names
        assert "Launch Scan" in action_names
        assert "Create Scan" in action_names
        assert "List Scan Templates" in action_names
        assert "Server Properties" in action_names
        assert "Server Status" in action_names
        assert "List Policies" in action_names
        assert "Delete Scans" in action_names
        assert "Export Scan Results" in action_names

    def test_python_sdk_clients(self):
        service = integration_service_factory.get_service_cls("nessus")
        clients = service.get_all_python_sdk_clients()
        assert isinstance(clients, list)
        assert len(clients) > 0
        methods = clients[0]["methods"]
        assert len(methods) == 18
        method_names = [m["client_method"] for m in methods]
        assert "server_properties" in method_names
        assert "list_scans" in method_names
        assert "create_scan" in method_names
        assert "launch_scan" in method_names
        assert "export_scan" in method_names


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

    def test_nessus_executor_branches(self):
        # 1. Missing client
        res = executor({"clients": {}})
        assert res == {"error": "Nessus client not found in context. Ensure integration is configured."}

        # 2. RequestException
        class MockClientException:
            def list_scans(self):
                raise requests.exceptions.RequestException("Connection failed")

        res = executor({"clients": {"nessus": MockClientException()}})
        assert "Failed to list scans due to network error: Connection failed" in res["error"]

        # 3. Invalid JSON (ValueError)
        class MockResponseInvalidJSON:
            status_code = 200
            def json(self):
                raise ValueError("No JSON object could be decoded")

        class MockClientInvalidJSON:
            def list_scans(self):
                return MockResponseInvalidJSON()

        res = executor({"clients": {"nessus": MockClientInvalidJSON()}})
        assert res == {"error": "Invalid JSON payload in response"}

        # 4. Invalid response schema (not dict or scans not list)
        class MockResponseInvalidSchema:
            status_code = 200
            def json(self):
                return {"scans": "invalid_not_a_list"}

        class MockClientInvalidSchema:
            def list_scans(self):
                return MockResponseInvalidSchema()

        res = executor({"clients": {"nessus": MockClientInvalidSchema()}})
        assert res == {"error": "Unexpected response schema from API: invalid 'scans' list"}

        # 5. Success case
        class MockResponseSuccess:
            status_code = 200
            def json(self):
                return {"scans": [{"id": 1, "name": "Scan 1"}]}

        class MockClientSuccess:
            def list_scans(self):
                return MockResponseSuccess()

        res = executor({"clients": {"nessus": MockClientSuccess()}})
        assert res == {"scans": [{"id": 1, "name": "Scan 1"}]}

        # 6. Non-200 status code
        class MockResponseNon200:
            status_code = 403
            text = "Forbidden"

        class MockClientNon200:
            def list_scans(self):
                return MockResponseNon200()

        res = executor({"clients": {"nessus": MockClientNon200()}})
        assert res == {"error": "Failed to list scans. Status code: 403", "details": "Forbidden"}
