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
    assert forms["label"] == "IPQualityScore (IPQS)"
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

def test_ipqs_execute_rest_api_task_key_injection():
    from unittest import mock

    class DummyPayloadTask:
        def __init__(self, executable, params=None):
            self.executable = executable
            self.params = params or []

    data = {
        "userId": "user123",
        "accountId": "acc123",
        "alias": "My IPQS",
        "cspName": "ipqs",
        "api_key": "test_key_123"
    }
    schema = IPQSIntegration(**data)
    service = IPQSService({}, schema)

    task = DummyPayloadTask("https://www.ipqualityscore.com/api/json/blocklist/list/{api_key}")

    called = []
    def mock_super_execute(task):
        called.append(task)
        return [], []
    
    with mock.patch("autobotAI_integrations.BaseService.execute_rest_api_task", side_effect=mock_super_execute):
        service.execute_rest_api_task(task)

    assert len(called) == 1
    assert task.executable == "https://www.ipqualityscore.com/api/json/blocklist/list/test_key_123"

def test_ipqs_sensitive_field_excluded():
    data = {
        "userId": "user123",
        "accountId": "acc123",
        "alias": "My IPQS",
        "cspName": "ipqs",
        "api_key": "test_key_123"
    }
    schema = IPQSIntegration(**data)
    dumped = schema.model_dump()
    assert "api_key" not in dumped, "api_key must be excluded from serialization"
