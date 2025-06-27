import pytest
import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassCloudflare:
    def test_cloudflare_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        cloudflare_query = "select * from cloudflare_user"
        task = sample_steampipe_task(integration, query=cloudflare_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"][:-2],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_python_sdk_api_key(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        
        python_code = """
def executor(context):
    cf = context["clients"]["cloudflare"]
    result = []
    try:
        accounts = cf.accounts.list()
        for account in accounts:
            result.append({
                "id": account.id,
                "name": account.name
            })
    except Exception as e:
        result.append({"error": str(e)})
    return [{"result": result}]
"""
        
        task = sample_python_task(
            integration, code=python_code, clients=["cloudflare"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_rest_api_creds_generation_api_key(self, get_keys, sample_integration_dict):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://api.cloudflare.com/client/v4"
        assert "X-Auth-Email" in creds.headers
        assert "X-Auth-Key" in creds.headers

    def test_python_sdk_creds_generation_api_key(self, get_keys, sample_integration_dict):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "CLOUDFLARE_EMAIL" in creds.envs
        assert "CLOUDFLARE_API_KEY" in creds.envs

    def test_cloudflare_steampipe_task_token(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        cloudflare_query = "select * from cloudflare_user"
        task = sample_steampipe_task(integration, query=cloudflare_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active_token(self, get_keys, sample_integration_dict):
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "token": get_keys["CLOUDFLARE_API_TOKEN"][:-1],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("cloudflare")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    def test_rest_api_action_run_token(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"token": get_keys["CLOUDFLARE_API_TOKEN"]}
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "User Details":
                continue
            
            task = sample_restapi_task(
                integration, action.code, action.parameters_definition
            )
            result = handle_task(task)
            print(result.model_dump_json(indent=2))
            test_result_format(result)
            action_ran = True
        assert action_ran

    def test_rest_api_action_run_api_key(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "api_key": get_keys["CLOUDFLARE_API_KEY"],
            "email": get_keys["CLOUDFLARE_EMAIL"],
        }
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "User Details":
                continue

            task = sample_restapi_task(
                integration, action.code, action.parameters_definition
            )
            result = handle_task(task)
            print(result.model_dump_json(indent=2))
            test_result_format(result)
            action_ran = True
        assert action_ran

    def test_python_sdk_token(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"token": get_keys["CLOUDFLARE_API_TOKEN"]}
        integration = sample_integration_dict("cloudflare", tokens)
        
        python_code = """
def executor(context):
    cf = context["clients"]["cloudflare"]
    result = []
    try:
        accounts = cf.accounts.list()
        for account in accounts:
            result.append({
                "id": account.id,
                "name": account.name
            })
    except Exception as e:
        result.append({"error": str(e)})
    return [{"result": result}]
"""
        
        task = sample_python_task(
            integration, code=python_code, clients=["cloudflare"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_rest_api_creds_generation_token(self, get_keys, sample_integration_dict):
        tokens = {"token": get_keys["CLOUDFLARE_API_TOKEN"]}
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://api.cloudflare.com/client/v4"
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation_token(self, get_keys, sample_integration_dict):
        tokens = {"token": get_keys["CLOUDFLARE_API_TOKEN"]}
        integration = sample_integration_dict("cloudflare", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "CLOUDFLARE_API_TOKEN" in creds.envs
