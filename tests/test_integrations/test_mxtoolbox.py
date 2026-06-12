import pytest
from autobotAI_integrations.integrations import integration_service_factory


class TestClassMXToolbox:
    
    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("mxtoolbox")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_integration_active_invalid_key(self, sample_integration_dict):
        # Using an invalid api_key format or value should return success: False
        tokens = {"api_key": "invalid-uuid-key"}
        integration = sample_integration_dict("mxtoolbox", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
        assert "Request failed with status code" in res["error"] or "Unauthorized" in res["error"] or "Forbidden" in res["error"]

    def test_mxtoolbox_python_sdk_task(self, sample_integration_dict, sample_python_task, test_result_format):
        tokens = {"api_key": ""} # Empty or dummy key works for example.com lookup
        integration = sample_integration_dict("mxtoolbox", tokens)
        code = """
def executor(context):
    client = context["clients"]["mxtoolbox"]
    response = client.lookup("dns", "example.com")
    if response.status_code == 200:
        return [response.json()]
    else:
        return [{"error": response.text}]
"""
        task = sample_python_task(integration, code=code, clients=["mxtoolbox"])
        from autobotAI_integrations.handlers.task_handler import handle_task
        result = handle_task(task)
        test_result_format(result)

    def test_get_details_flags(self):
        service = integration_service_factory.get_service_cls("mxtoolbox")
        details = service.get_details()
        assert details["preview"] is True

