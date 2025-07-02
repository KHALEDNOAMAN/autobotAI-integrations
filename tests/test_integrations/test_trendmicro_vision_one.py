import pytest
import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassTrendMicroVisionOne:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"][:-2]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("trendmicro_vision_one")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "Check availability of API service":
                continue
            try:
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
                test_result_format(result)
                action_ran = True
            except Exception as e:
                traceback.print_exc()
        assert action_ran

    def test_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        
        python_code = """
def executor(context):
    client = context["clients"]["trendmicro_vision_one"]
    result = []
    try:
        # Get workbench alerts
        alerts = client.workbench.get_alerts()
        for alert in alerts:
            result.append({
                "id": alert.id,
                "severity": alert.severity,
                "description": alert.description
            })
    except Exception as e:
        result.append({"error": str(e)})
    return [{"result": result}]
"""
        
        task = sample_python_task(
            integration, code=python_code, clients=["trendmicro_vision_one"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_rest_api_creds_generation(self, get_keys, sample_integration_dict):
        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://api.xdr.trendmicro.com"
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        tokens = {"api_key": get_keys["TRENDMICRO_API_KEY"]}
        integration = sample_integration_dict("trendmicro_vision_one", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "TRENDMICRO_API_KEY" in creds.envs
        assert "TRENDMICRO_BASE_URL" in creds.envs