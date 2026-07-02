from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

crowdstrike_edr_python_code = """
def executor(context):
    detects = context["clients"]["detects"]
    response = detects.query_detects(limit=10)
    return [{"result": response}]
"""


def _get_tokens(get_keys):
    if not get_keys.get("CROWDSTRIKE_CLIENT_ID") or not get_keys.get(
        "CROWDSTRIKE_CLIENT_SECRET"
    ):
        return None
    return {
        "client_cloud": get_keys.get("CROWDSTRIKE_CLOUD", "us-2"),
        "client_id": get_keys["CROWDSTRIKE_CLIENT_ID"],
        "client_secret": get_keys["CROWDSTRIKE_CLIENT_SECRET"],
    }


class TestClassCrowdstrikeEDR:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike_edr", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

        tokens = {
            **tokens,
            "client_secret": tokens["client_secret"][0:-2],
        }
        integration = sample_integration_dict("crowdstrike_edr", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self):
        service = integration_service_factory.get_service_cls("crowdstrike_edr")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike_edr", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "Query detections by filter":
                continue
            task = sample_restapi_task(
                integration, action.code, action.parameters_definition
            )
            result = handle_task(task)
            test_result_format(result)
            action_ran = True
        assert action_ran

    def test_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike_edr", tokens)
        task = sample_python_task(
            integration,
            code=crowdstrike_edr_python_code,
            clients=["detects"],
        )
        result = handle_task(task)
        test_result_format(result)

    def test_rest_api_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike_edr", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert "api.us-2.crowdstrike.com" in creds.base_url or "api.crowdstrike.com" in creds.base_url
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike_edr", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "FALCON_CLIENT_ID" in creds.envs
        assert "FALCON_CLIENT_SECRET" in creds.envs
        assert "FALCON_CLOUD" in creds.envs

    def test_get_details_flags(self):
        service = integration_service_factory.get_service_cls("crowdstrike_edr")
        details = service.get_details()
        assert details["preview"] is True
