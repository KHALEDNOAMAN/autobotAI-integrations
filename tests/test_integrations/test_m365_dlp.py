import traceback
from unittest.mock import MagicMock, patch

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.m365_dlp import M365DLPIntegration, M365DLPService
from autobotAI_integrations.models import ConnectionInterfaces


def _get_tokens(get_keys):
    if not get_keys.get("M365_DLP_TENANT_ID"):
        return None
    if not get_keys.get("M365_DLP_CLIENT_ID"):
        return None
    if not get_keys.get("M365_DLP_CLIENT_SECRET"):
        return None
    return {
        "tenant_id": get_keys["M365_DLP_TENANT_ID"],
        "client_id": get_keys["M365_DLP_CLIENT_ID"],
        "client_secret": get_keys["M365_DLP_CLIENT_SECRET"],
    }


class TestM365DLP:

    def test_schema_defaults(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env — set M365_DLP_TENANT_ID, M365_DLP_CLIENT_ID, M365_DLP_CLIENT_SECRET")

        integration_dict = sample_integration_dict("m365_dlp", tokens)
        integration = M365DLPIntegration(**integration_dict)
        assert integration.name == "Microsoft 365 DLP"
        assert integration.category == "security_tools"

    def test_sensitive_field_excluded(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration_dict = sample_integration_dict("m365_dlp", tokens)
        integration = M365DLPIntegration(**integration_dict)
        dumped = integration.model_dump()
        assert "client_secret" not in dumped

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"], "Dummy env credentials should fail authentication"
        assert res.get("error")

        tokens = {**tokens, "client_secret": tokens["client_secret"][0:-2]}
        integration = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_integration_active_success_when_token_and_api_succeed(
        self, get_keys, sample_integration_dict
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration_dict = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration_dict)

        token_response = MagicMock()
        token_response.ok = True
        token_response.json.return_value = {"access_token": "dummy-token"}

        alerts_response = MagicMock()
        alerts_response.status_code = 200
        alerts_response.text = ""

        with patch(
            "autobotAI_integrations.integrations.m365_dlp.requests.post",
            return_value=token_response,
        ), patch(
            "autobotAI_integrations.integrations.m365_dlp.requests.get",
            return_value=alerts_response,
        ):
            result = service._test_integration()

        assert result["success"] is True

    def test_integration_active_fails_on_invalid_token_response(
        self, get_keys, sample_integration_dict
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration_dict = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration_dict)

        token_response = MagicMock()
        token_response.ok = False
        token_response.status_code = 401
        token_response.text = "invalid_client"

        with patch(
            "autobotAI_integrations.integrations.m365_dlp.requests.post",
            return_value=token_response,
        ):
            result = service._test_integration()

        assert not result["success"]
        assert "Authentication failed" in result["error"]

    def test_actions_generation(self):
        actions = M365DLPService.get_all_rest_api_actions()
        assert len(actions) > 0
        for action in actions:
            assert action.name and action.name.strip()
        action_names = " ".join(action.name.lower() for action in actions)
        assert "alert" in action_names
        assert "audit" in action_names

    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()

        alerts_response = MagicMock()
        alerts_response.status_code = 200
        alerts_response.json.return_value = {"value": []}
        alerts_response.text = '{"value": []}'

        action_ran = False
        for action in actions:
            if action.name != "List DLP security alerts":
                continue
            try:
                with patch.object(
                    M365DLPService, "_get_access_token", return_value="dummy-token"
                ), patch(
                    "autobotAI_integrations.requests.request",
                    return_value=alerts_response,
                ):
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                print(result.model_dump_json(indent=2))
                test_result_format(result)
                action_ran = True
            except Exception:
                traceback.print_exc()
        assert action_ran

    def test_rest_api_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration)

        token_response = MagicMock()
        token_response.ok = True
        token_response.json.return_value = {"access_token": "dummy-token"}

        with patch(
            "autobotAI_integrations.integrations.m365_dlp.requests.post",
            return_value=token_response,
        ):
            creds = service.generate_rest_api_creds()

        assert creds.base_url == "https://graph.microsoft.com"
        assert "Authorization" in creds.headers
        assert creds.headers["Authorization"].startswith("Bearer ")

    def test_python_sdk_creds_generation(self, get_keys, sample_integration_dict):
        tokens = _get_tokens(get_keys)
        if not tokens:
            pytest.skip("M365 DLP dummy keys not in .env")

        integration = sample_integration_dict("m365_dlp", tokens)
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert creds.envs["AZURE_TENANT_ID"] == tokens["tenant_id"]
        assert creds.envs["AZURE_CLIENT_ID"] == tokens["client_id"]
        assert creds.envs["AZURE_CLIENT_SECRET"] == tokens["client_secret"]

