from unittest.mock import MagicMock, patch

from autobotAI_integrations.integrations.palo_alto_scm import (
    PaloAltoSCMIntegration,
    PaloAltoSCMService,
)
from autobotAI_integrations.integrations.palo_alto_scm.scm_client import (
    PaloAltoSCMClient,
)


def test_palo_alto_scm_schema_validation():
    data = {
        "auth_url": "https://auth.apps.paloaltonetworks.com/oauth2/access_token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "host": "api.strata.paloaltonetworks.com",
        "protocol": "https",
        "scope": "tsg_id:1234567890",
        "alias": "palo_alto_scm_alias",
        "userId": "test_user",
        "cspName": "palo_alto_scm",
    }
    integration = PaloAltoSCMIntegration(**data)
    assert integration.client_id == "test_client_id"
    assert integration.client_secret == "test_client_secret"
    assert integration.scope == "tsg_id:1234567890"
    assert integration.host == "api.strata.paloaltonetworks.com"
    assert integration.protocol == "https"
    assert integration.auth_url.endswith("/oauth2/access_token")
    assert integration.alias == "palo_alto_scm_alias"
    assert integration.name == "Palo Alto Strata Cloud Manager"
    assert integration.category == "security_tools"


def test_palo_alto_scm_defaults():
    integration = PaloAltoSCMIntegration(
        **{
            "client_id": "id",
            "client_secret": "secret",
            "scope": "tsg_id:1",
            "alias": "alias",
            "userId": "user",
            "cspName": "palo_alto_scm",
        }
    )
    assert integration.auth_url == "https://auth.apps.paloaltonetworks.com/oauth2/access_token"
    assert integration.host == "api.strata.paloaltonetworks.com"
    assert integration.protocol == "https"


def test_palo_alto_scm_service_metadata():
    forms = PaloAltoSCMService.get_forms()
    assert "children" in forms
    field_names = [f["name"] for f in forms["children"]]
    assert "client_id" in field_names
    assert "client_secret" in field_names
    assert "scope" in field_names
    assert "auth_url" in field_names
    assert "host" in field_names
    assert "protocol" in field_names

    interfaces = PaloAltoSCMService.supported_connection_interfaces()
    interface_names = [i.name for i in interfaces]
    assert "REST_API" in interface_names
    assert "PYTHON_SDK" in interface_names
    assert "STEAMPIPE" not in interface_names
    assert "MCP_SERVER" not in interface_names

    details = PaloAltoSCMService.get_details()
    assert details.get("preview") is True


def test_palo_alto_scm_test_integration_success():
    integration = {
        "auth_url": "https://auth.apps.paloaltonetworks.com/oauth2/access_token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "host": "api.strata.paloaltonetworks.com",
        "protocol": "https",
        "scope": "tsg_id:1234567890",
        "alias": "alias",
        "userId": "user",
        "cspName": "palo_alto_scm",
    }
    service = PaloAltoSCMService({}, integration)

    token_response = MagicMock()
    token_response.ok = True
    token_response.json.return_value = {
        "access_token": "test-token",
        "expires_in": 300,
    }

    devices_response = MagicMock()
    devices_response.status_code = 200
    devices_response.json.return_value = {"data": []}

    with patch("autobotAI_integrations.integrations.palo_alto_scm.requests.post", return_value=token_response) as mock_post, \
         patch("autobotAI_integrations.integrations.palo_alto_scm.requests.get", return_value=devices_response) as mock_get:
        result = service._test_integration()

    assert result == {"success": True}
    mock_post.assert_called_once()
    mock_get.assert_called_once()
    assert mock_get.call_args.args[0].endswith("/config/setup/v1/devices")


def test_palo_alto_scm_generate_rest_api_creds():
    integration = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scope": "tsg_id:1234567890",
        "alias": "alias",
        "userId": "user",
        "cspName": "palo_alto_scm",
    }
    service = PaloAltoSCMService({}, integration)

    token_response = MagicMock()
    token_response.ok = True
    token_response.json.return_value = {
        "access_token": "rest-token",
        "expires_in": 300,
    }

    with patch(
        "autobotAI_integrations.integrations.palo_alto_scm.requests.post",
        return_value=token_response,
    ):
        creds = service.generate_rest_api_creds()

    assert creds.base_url == "https://api.strata.paloaltonetworks.com"
    assert creds.token == "rest-token"
    assert creds.headers["Authorization"] == "Bearer rest-token"


def test_palo_alto_scm_generate_python_sdk_creds():
    integration = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scope": "tsg_id:1234567890",
        "alias": "alias",
        "userId": "user",
        "cspName": "palo_alto_scm",
    }
    service = PaloAltoSCMService({}, integration)
    creds = service.generate_python_sdk_creds()
    assert creds.envs["PALO_ALTO_SCM_CLIENT_ID"] == "test_client_id"
    assert creds.envs["PALO_ALTO_SCM_CLIENT_SECRET"] == "test_client_secret"
    assert creds.envs["PALO_ALTO_SCM_SCOPE"] == "tsg_id:1234567890"
    assert creds.envs["PALO_ALTO_SCM_HOST"] == "api.strata.paloaltonetworks.com"
    assert creds.envs["PALO_ALTO_SCM_PROTOCOL"] == "https"


def test_palo_alto_scm_client_request_injects_bearer():
    client = PaloAltoSCMClient(
        protocol="https",
        host="api.strata.paloaltonetworks.com",
        auth_url="https://auth.apps.paloaltonetworks.com/oauth2/access_token",
        client_id="cid",
        client_secret="csecret",
        scope="tsg_id:1",
    )

    token_response = MagicMock()
    token_response.raise_for_status = MagicMock()
    token_response.json.return_value = {
        "access_token": "cached-token",
        "expires_in": 300,
    }

    api_response = MagicMock()
    api_response.status_code = 200

    with patch.object(client.session, "post", return_value=token_response) as mock_post, \
         patch.object(client.session, "request", return_value=api_response) as mock_request:
        response = client.request("GET", "/config/setup/v1/devices")

    assert response is api_response
    mock_post.assert_called_once()
    called_headers = mock_request.call_args.kwargs["headers"]
    assert called_headers["Authorization"] == "Bearer cached-token"
    assert mock_request.call_args.args[0] == "GET"
    assert mock_request.call_args.args[1].endswith("/config/setup/v1/devices")
