import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

microsoft_defender_python_code = """

def executor(context):
    res = []
    client = context["clients"]["msgraph-defender"]
    
    return res
"""


def _get_tokens(get_keys):
    if not get_keys.get("AZURE_TENANT_ID") or not get_keys.get("AZURE_CLIENT_ID"):
        return None
    if not get_keys.get("AZURE_CLIENT_SECRET"):
        return None
    return {
        "tenant_id": get_keys["AZURE_TENANT_ID"],
        "client_id": get_keys["AZURE_CLIENT_ID"],
        "client_secret": get_keys["AZURE_CLIENT_SECRET"],
    }


class TestClassMicrosoftDefender:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("microsoft_defender", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"], f"Integration connection failed: {res.get('error')}"

        tokens = {**tokens, "client_secret": tokens["client_secret"][0:-2]}
        integration = sample_integration_dict("microsoft_defender", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("microsoft_defender")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("microsoft_defender", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name != "List alerts":
                continue
            try:
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                test_result_format(result)
                print(result.model_dump_json(indent=2))
            except Exception:
                traceback.print_exc()
            
    def test_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("microsoft_defender", tokens)
        task = sample_python_task(
            integration,
            code=microsoft_defender_python_code,
            clients=["msgraph-defender"],
        )
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))

    def test_rest_api_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("microsoft_defender", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://api.security.microsoft.com"
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("microsoft_defender", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "AZURE_TENANT_ID" in creds.envs
        assert "AZURE_CLIENT_ID" in creds.envs
        assert "AZURE_CLIENT_SECRET" in creds.envs

    def test_get_details_flags(self):
        service = integration_service_factory.get_service_cls("microsoft_defender")
        details = service.get_details()
        assert details["preview"] is True

