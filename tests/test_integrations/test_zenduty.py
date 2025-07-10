from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
import traceback


class TestClassZenduty:
    def test_zenduty_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {"api_token": get_keys["ZENDUTY_API_TOKEN"]}
        integration = sample_integration_dict("zenduty", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "api_token": get_keys["ZENDUTY_API_TOKEN"][3:-3],
        }
        integration = sample_integration_dict("zenduty", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("zenduty")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Create the Event object":
                assert action.code.startswith("https://events.zenduty.com")
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0
    
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"api_token": get_keys["ZENDUTY_API_TOKEN"]}
        integration = sample_integration_dict("zenduty", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        ran = False
        for action in actions:
            if action.name ==  "List all Account Member objects":
                # In most Cases this will fail as parameters_definition does not contains actual values
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
                test_result_format(result)
                ran = True
                break
        assert ran

    def test_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"api_token": get_keys["ZENDUTY_API_TOKEN"]}
        integration = sample_integration_dict("zenduty", tokens)
        
        python_code = """
def executor(context):
    zenduty = context["clients"]["zenduty"]
    api_client = context["clients"]["api_client"]
    result = []
    try:
        api_obj = zenduty.TeamsApi(api_client)
        response = api_obj.get_teams()
        result.append({
            "teams_data": response.json(),
        })
    except Exception as e:
        result.append({"error": str(e)})
    return [{"result": result}]
"""
        
        task = sample_python_task(
            integration, code=python_code, clients=["zenduty", "api_client"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        tokens = {"api_token": get_keys["ZENDUTY_API_TOKEN"]}
        integration = sample_integration_dict("zenduty", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "ZENDUTY_API_TOKEN" in creds.envs