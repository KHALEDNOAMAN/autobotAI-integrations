from autobotAI_integrations.integrations.nessus import NessusService, NessusIntegration
from autobotAI_integrations.models import RestAPICreds


class TestNessusIntegration:
    def test_schema_validation(self):
        schema = NessusService.get_schema()
        assert schema is NessusIntegration

        # Should raise error if required fields are missing
        # url has default, but access_key and secret_key are required
        try:
            NessusIntegration(url="https://test:8834")
            assert False, "Should have raised validation error for missing keys"
        except Exception:
            pass

        # Valid schema
        valid = NessusIntegration(
            url="https://test:8834",
            access_key="my_access_key",
            secret_key="my_secret_key"
        )
        assert valid.url == "https://test:8834"

    def test_get_details(self):
        details = NessusService.get_details()
        assert "clients" in details
        assert details["supported_executor"] == "ecs"
        assert details["compliance_supported"] is False
        assert "supported_interfaces" in details
        assert "python_code_sample" in details
        
        # Verify the requested "preview" tag is present
        assert details.get("preview") is True

    def test_get_python_sdk_client(self):
        creds = RestAPICreds(
            url="https://test:8834",
            access_key="my_access_key",
            secret_key="my_secret_key"
        )
        client_wrapper = NessusService.get_python_sdk_client(creds, None)
        
        # Access the underlying NessusClient
        client = client_wrapper.client
        assert client.url == "https://test:8834"
        assert client.access_key == "my_access_key"
        assert client.secret_key == "my_secret_key"
