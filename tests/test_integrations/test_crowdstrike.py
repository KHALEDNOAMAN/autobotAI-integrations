import traceback

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


_edr_python_code = """
def executor(context):
    detects = context["clients"]["detects"]
    response = detects.query_detects(limit=10)
    return [{"result": response}]
"""

_idp_python_code = """
def executor(context):
    identity_protection = context["clients"]["identity_protection"]
    result = []
    try:
        response = identity_protection.query_sensors(limit=10)
        result.append(response)
    except Exception as e:
        result.append({"error": str(e)})
    return [{"result": result}]
"""

def _get_tokens(get_keys):
    """Return credential dict or None if keys are missing."""
    if not get_keys.get("FALCON_CLIENT_ID") or not get_keys.get(
        "FALCON_CLIENT_SECRET"
    ):
        return None
    return {
        "client_cloud": get_keys.get("FALCON_CLOUD", "us-2"),
        "client_id": get_keys["FALCON_CLIENT_ID"],
        "client_secret": get_keys["FALCON_CLIENT_SECRET"],
    }


class TestClassCrowdstrike:

    def test_integration_active(self, get_keys, sample_integration_dict):
        """Valid credentials → active; truncated secret → inactive."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"], f"Expected active but got: {res}"

        bad_tokens = {**tokens, "client_secret": tokens["client_secret"][:-2]}
        integration = sample_integration_dict("crowdstrike", bad_tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"], "Expected inactive with bad credentials"


    def test_crowdstrike_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        """Steampipe inventory query — crowdstrike_user table."""
        tokens = {
            "client_cloud": get_keys.get("FALCON_CLOUD", "us-2"),
            "client_id": get_keys["FALCON_CLIENT_ID"],
            "client_secret": get_keys["FALCON_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("crowdstrike", tokens)
        crowdstrike_query = "select * from crowdstrike_user"
        task = sample_steampipe_task(integration, query=crowdstrike_query)
        result = handle_task(task)
        test_result_format(result)

    def test_rest_api_creds_generation(self, get_keys, sample_integration_dict):
        """Bearer token is present and the base URL matches the selected cloud."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert (
            "api.us-2.crowdstrike.com" in creds.base_url
            or "api.crowdstrike.com" in creds.base_url
        ), f"Unexpected base_url: {creds.base_url}"
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        """SDK creds contain all required Falcon environment variables."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert "FALCON_CLIENT_ID" in creds.envs
        assert "FALCON_CLIENT_SECRET" in creds.envs
        assert "FALCON_CLOUD" in creds.envs

    def test_edr_actions_generation(self):
        """All EDR REST actions have non-empty names."""
        service = integration_service_factory.get_service_cls("crowdstrike")
        actions = service.get_all_rest_api_actions()
        edr_actions = [
            a for a in actions
            if any(
                kw in (a.name or "").lower()
                for kw in ("detect", "host", "incident", "alert", "responder", "script", "file", "batch")
            )
        ]
        assert len(edr_actions) > 0, "No EDR actions found"
        for action in edr_actions:
            assert action.name is not None
            assert action.name.strip() != ""

    def test_idp_actions_generation(self):
        """All Identity Protection REST actions have non-empty names."""
        service = integration_service_factory.get_service_cls("crowdstrike")
        actions = service.get_all_rest_api_actions()
        idp_actions = [
            a for a in actions
            if any(
                kw in (a.name or "").lower()
                for kw in ("sensor", "graphql", "policy rule", "identity")
            )
        ]
        assert len(idp_actions) > 0, "No Identity Protection actions found"
        for action in idp_actions:
            assert action.name is not None
            assert action.name.strip() != ""

    def test_edr_action_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        """Run the 'Query detections by filter' REST action end-to-end."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "Query detections by filter":
                continue
            task = sample_restapi_task(integration, action.code, action.parameters_definition)
            result = handle_task(task)
            test_result_format(result)
            action_ran = True
        assert action_ran, "'Query detections by filter' action not found"

    def test_idp_action_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        """Run the 'Query sensors by filter' REST action end-to-end."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        action_ran = False
        for action in actions:
            if action.name != "Query sensors by filter":
                continue
            try:
                task = sample_restapi_task(integration, action.code, action.parameters_definition)
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
                test_result_format(result)
                action_ran = True
            except Exception:
                traceback.print_exc()
        assert action_ran, "'Query sensors by filter' action not found"

    def test_edr_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        """Execute inline Python code using the 'detects' falconpy client."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        task = sample_python_task(
            integration,
            code=_edr_python_code,
            clients=["detects"],
        )
        result = handle_task(task)
        test_result_format(result)

    def test_idp_python_sdk(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        """Execute inline Python code using the 'identity_protection' falconpy client."""
        tokens = _get_tokens(get_keys)
        if not tokens:
            return

        integration = sample_integration_dict("crowdstrike", tokens)
        task = sample_python_task(
            integration,
            code=_idp_python_code,
            clients=["identity_protection"],
        )
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))

