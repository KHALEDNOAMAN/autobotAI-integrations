import pytest
from autobotAI_integrations.integrations.proofpoint_itm import ProofpointITMIntegration, ProofpointITMService

def test_proofpoint_itm_schema_validation():
    # Valid data
    data = {
        "base_url": "https://tenant.itmsaas.proofpoint.com",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "alias": "proofpoint_itm_alias",
        "userId": "test_user",
        "cspName": "aws"
    }
    integration = ProofpointITMIntegration(**data)
    assert integration.base_url == "https://tenant.itmsaas.proofpoint.com"
    assert integration.client_id == "test_client_id"
    assert integration.client_secret == "test_client_secret"
    assert integration.alias == "proofpoint_itm_alias"
    assert integration.name == "Endpoint DLP"
    assert integration.category == "security_tools"

def test_proofpoint_itm_service_metadata():
    forms = ProofpointITMService.get_forms()
    assert "children" in forms
    # verify the fields are generated
    field_names = [f["name"] for f in forms["children"]]
    assert "base_url" in field_names
    assert "client_id" in field_names
    assert "client_secret" in field_names

    interfaces = ProofpointITMService.supported_connection_interfaces()
    assert "REST_API" in [i.name for i in interfaces]
