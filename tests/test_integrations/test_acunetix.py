import pytest
from unittest.mock import patch, MagicMock
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.acunetix import (
    AcunetixIntegration,
    AcunetixService,
)


class TestAcunetix:
    def test_schema_defaults(self):
        """Test default schema parameters."""
        schema = AcunetixIntegration(
            userId="user-123",
            cspName="csp-acunetix",
            alias="Acunetix Test",
            api_key="acunetix-key"
        )
        assert schema.url == "https://online.acunetix.com/api/v1"
        assert schema.verify_ssl is False
        assert schema.name == "Acunetix Web Application Security"

    def test_connection_interfaces(self):
        """Supported interface should be REST_API."""
        interfaces = AcunetixService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_rest_api_credentials_generation(self, sample_integration_dict):
        """Verify generated rest API credentials structure."""
        d = sample_integration_dict(
            "acunetix",
            {
                "url": "https://online.acunetix.com/api/v1",
                "api_key": "acunetix-secret-token",
                "verify_ssl": True
            }
        )
        service = AcunetixService({}, d)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://online.acunetix.com/api/v1"
        assert creds.headers == {
            "X-Auth": "acunetix-secret-token",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        assert creds.verify_ssl is True

    @patch("requests.get")
    def test_connection_verification_success(self, mock_get, sample_integration_dict):
        """Test successful connection testing return value."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        d = sample_integration_dict(
            "acunetix",
            {
                "url": "https://online.acunetix.com/api/v1",
                "api_key": "test-key",
            }
        )
        service = AcunetixService({}, d)
        result = service._test_integration()
        assert result == {"success": True}
        mock_get.assert_called_once_with(
            "https://online.acunetix.com/api/v1/targets",
            params={"limit": 1},
            headers={
                "X-Auth": "test-key",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=15
        )

    @patch("requests.get")
    def test_connection_verification_failure(self, mock_get, sample_integration_dict):
        """Test connection testing failure return value."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        d = sample_integration_dict(
            "acunetix",
            {
                "url": "https://online.acunetix.com/api/v1",
                "api_key": "bad-key",
            }
        )
        service = AcunetixService({}, d)
        result = service._test_integration()
        assert result["success"] is False
        assert "401" in result["error"]
