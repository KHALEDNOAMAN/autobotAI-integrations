import pytest
from autobotAI_integrations.integrations.proofpoint_email_security import ProofpointEmailSecurityService, ProofpointEmailSecurityIntegration
from autobotAI_integrations.models import IntegrationCategory

def test_proofpoint_email_security_forms():
    forms = ProofpointEmailSecurityService.get_forms()
    assert forms["label"] == "Proofpoint Email Security"
    assert forms["type"] == "form"
    assert len(forms["children"]) == 2
    assert forms["children"][0]["name"] == "principal"
    assert forms["children"][1]["name"] == "secret"

def test_proofpoint_email_security_category():
    assert ProofpointEmailSecurityService.get_category() == IntegrationCategory.SECURITY_TOOLS.value

def test_proofpoint_email_security_creds():
    integration = ProofpointEmailSecurityIntegration(
        principal="test_principal",
        secret="test_secret",
        userId="test_user",
        cspName="test_csp",
        alias="test_alias"
    )
    service = ProofpointEmailSecurityService(integration)
    creds = service.generate_rest_api_creds()
    assert creds.base_url == "https://tap-api-v2.proofpoint.com/v2"
    assert creds.auth == ("test_principal", "test_secret")
