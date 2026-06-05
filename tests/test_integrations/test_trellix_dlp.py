import pytest
from autobotAI_integrations.integrations.trellix_dlp import TrellixDLPIntegration, TrellixDLPService

def test_trellix_dlp_schema_validation():
    # Valid data
    data = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "api_key": "test_api_key",
        "alias": "trellix_dlp_alias",
        "userId": "test_user",
        "cspName": "aws"
    }
    integration = TrellixDLPIntegration(**data)
    assert integration.client_id == "test_client_id"
    assert integration.client_secret == "test_client_secret"
    assert integration.api_key == "test_api_key"
    assert integration.alias == "trellix_dlp_alias"
    assert integration.name == "Trellix DLP"
    assert integration.category == "security_tools"

def test_trellix_dlp_service_metadata():
    forms = TrellixDLPService.get_forms()
    assert "children" in forms
    # verify the fields are generated
    field_names = [f["name"] for f in forms["children"]]
    assert "client_id" in field_names
    assert "client_secret" in field_names
    assert "api_key" in field_names

    interfaces = TrellixDLPService.supported_connection_interfaces()
    assert "REST_API" in [i.name for i in interfaces]
