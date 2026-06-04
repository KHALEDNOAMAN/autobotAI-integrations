import pytest
from autobotAI_integrations.integrations.ipqs import IPQSIntegration, IPQSService

def test_ipqs_schema():
    data = {
        "userId": "user123",
        "accountId": "acc123",
        "alias": "My IPQS",
        "cspName": "ipqs",
        "api_key": "test_key_123"
    }
    schema = IPQSIntegration(**data)
    assert schema.api_key == "test_key_123"
    assert schema.alias == "My IPQS"

def test_ipqs_service_get_forms():
    forms = IPQSService.get_forms()
    assert forms["label"] == "IPQS"
    assert len(forms["children"]) == 1
    assert forms["children"][0]["name"] == "api_key"

def test_ipqs_generate_rest_api_creds():
    data = {
        "userId": "user123",
        "accountId": "acc123",
        "alias": "My IPQS",
        "cspName": "ipqs",
        "api_key": "test_key_123"
    }
    schema = IPQSIntegration(**data)
    service = IPQSService({}, schema)
    creds = service.generate_rest_api_creds()
    
    assert creds.base_url == "https://www.ipqualityscore.com/api/json"
    assert creds.headers["IPQS-KEY"] == "test_key_123"
