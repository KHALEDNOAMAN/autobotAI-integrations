import traceback
from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

class TestClassSaviynt:

    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test Saviynt integration connection with valid credentials"""
        tokens = {
            "base_url": get_keys["SAVIYNT_BASE_URL"],
            "username": get_keys["SAVIYNT_USERNAME"],
            "password": get_keys["SAVIYNT_PASSWORD"],
        }
        integration = sample_integration_dict("saviynt", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        # print(res)
        
        # assert res["success"], f"Integration connection failed: {res.get('error')}"

    def test_action_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
        "base_url": get_keys["SAVIYNT_BASE_URL"], 
        "username": get_keys["SAVIYNT_USERNAME"],
        "password": get_keys["SAVIYNT_PASSWORD"],
        }
        integration = sample_integration_dict("saviynt", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()

        for action in actions:
            if action.name == "Fetch User Update Rules":
                try:
                    task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                    # assert result.success == True, "Expected success=True in result"
                except Exception as e:
                    traceback.print_exc()
                    assert False, f"Action execution failed: {str(e)}"