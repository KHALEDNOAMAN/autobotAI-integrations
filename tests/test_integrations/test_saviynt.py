import traceback
from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

class TestClassSaviynt:

    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test Saviynt integration connection with valid credentials"""
        tokens = {
            "base_url": get_keys["SAVIYNT_BASE_URL"],
            "token": get_keys["SAVIYNT_TOKEN"],
        }
        integration = sample_integration_dict("saviynt", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"], f"Integration connection failed: {res.get('error')}"

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("saviynt")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_action_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
        "base_url": get_keys["SAVIYNT_BASE_URL"],
        "token": get_keys["SAVIYNT_TOKEN"],
        }
        integration = sample_integration_dict("saviynt", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Get SavRoles":
                try:
                    task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()
                    assert False, f"Action execution failed: {str(e)}"
                
        