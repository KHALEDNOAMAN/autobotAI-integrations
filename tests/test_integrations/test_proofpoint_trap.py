import pytest
from autobotAI_integrations.integrations.proofpoint_trap import ProofpointTRAPIntegration, ProofpointTRAPService

def test_proofpoint_trap_schema_validation():
    # Valid data
    data = {
        "base_url": "https://trap.example.com",
        "principal": "test_principal",
        "secret": "test_secret",
        "alias": "proofpoint_trap_alias",
        "userId": "test_user",
        "cspName": "aws"
    }
    integration = ProofpointTRAPIntegration(**data)
    assert integration.base_url == "https://trap.example.com"
    assert integration.principal == "test_principal"
    assert integration.secret == "test_secret"
    assert integration.alias == "proofpoint_trap_alias"
    assert integration.name == "Proofpoint TRAP"
    assert integration.category == "security_tools"

def test_proofpoint_trap_service_metadata():
    forms = ProofpointTRAPService.get_forms()
    assert "children" in forms
    # verify the fields are generated
    field_names = [f["name"] for f in forms["children"]]
    assert "base_url" in field_names
    assert "principal" in field_names
    assert "secret" in field_names

    interfaces = ProofpointTRAPService.supported_connection_interfaces()
    assert "REST_API" in [i.name for i in interfaces]
