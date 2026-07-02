import json
from pathlib import Path

import pytest
import requests

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.symphony_summit import (
    DEFAULT_API_PATH,
    DEFAULT_ORG_ID,
    DEFAULT_PROXY_ID,
    SymphonySummitIntegration,
    SymphonySummitService,
)
from autobotAI_integrations.models import ConnectionInterfaces

DUMMY_TOKENS = {
    "base_url": "https://demo.symphonysummit.com",
    "api_key": "dummy-symphony-api-key",
}

EXPECTED_ACTION_COUNT = 10
EXPECTED_SERVICE_NAMES = {
    "SR_GetServiceCatalogDetails",
    "SR_GetSelectedCatalogDetailsList",
    "SR_LogServiceRequestCatalog",
    "SR_GetServiceRequestListDetails",
    "SR_UpdateServiceRequest",
    "IM_GetIncidentDetailsAndChangeHistory",
    "IM_GetIncidentListDetails",
    "IM_LogOrUpdateIncident",
    "CM_GetCR_Master",
    "CM_LogOrUpdateCR",
}


@pytest.fixture
def dummy_symphony_summit(sample_integration_dict):
    return sample_integration_dict("symphony_summit", DUMMY_TOKENS)


class TestSymphonySummit:
    def test_factory_registration(self):
        cls = integration_service_factory.get_service_cls("symphony_summit")
        assert cls is SymphonySummitService

    def test_schema_defaults(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "test-key",
            },
        )
        integration = SymphonySummitIntegration(**d)
        assert integration.name == "Symphony Summit"
        assert integration.category == "notifications_and_communications"

    def test_api_url(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "key",
            },
        )
        integration = SymphonySummitIntegration(**d)
        assert (
            integration.api_url
            == "https://demo.symphonysummit.com" + DEFAULT_API_PATH
        )

    def test_api_url_full_endpoint(self, sample_integration_dict):
        full_url = (
            "https://demo.symphonysummit.com/REST/"
            "Summit_RESTWCF.svc/RESTService/CommonWS_JsonObjCall"
        )
        d = sample_integration_dict(
            "symphony_summit",
            {"base_url": full_url, "api_key": "key"},
        )
        integration = SymphonySummitIntegration(**d)
        assert integration.api_url == full_url

    def test_proxy_details_defaults(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "my-api-key",
            },
        )
        integration = SymphonySummitIntegration(**d)
        proxy = integration.proxy_details()
        assert proxy["AuthType"] == "APIKEY"
        assert proxy["APIKey"] == "my-api-key"
        assert proxy["ProxyID"] == DEFAULT_PROXY_ID
        assert proxy["OrgID"] == DEFAULT_ORG_ID
        assert proxy["ReturnType"] == "JSON"
        assert proxy["TokenID"] == ""

    def test_auth_probe_body(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "stored-key",
            },
        )
        service = integration_service_factory.get_service(None, d)
        body = service._build_auth_probe_body()
        proxy = body["objCommonParameters"]["_ProxyDetails"]
        assert proxy["APIKey"] == "stored-key"
        assert body["ServiceName"] == "IM_GetIncidentDetailsAndChangeHistory"
        assert body["objCommonParameters"]["TicketNo"] == 0

    def test_evaluate_auth_probe_success(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {"base_url": "https://demo.symphonysummit.com", "api_key": "key"},
        )
        service = integration_service_factory.get_service(None, d)

        class FakeResponse:
            status_code = 200
            headers = {"Content-Type": "application/json"}
            text = '{"Errors": ""}'

        result = service._evaluate_auth_probe(FakeResponse(), {"Errors": ""})
        assert result["success"] is True
        assert "authenticated" in result["message"].lower()

    def test_evaluate_auth_probe_auth_failure(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {"base_url": "https://demo.symphonysummit.com", "api_key": "key"},
        )
        service = integration_service_factory.get_service(None, d)

        class FakeResponse:
            status_code = 200
            headers = {"Content-Type": "application/json"}
            text = ""

        result = service._evaluate_auth_probe(
            FakeResponse(), {"Errors": "Invalid API Key"}
        )
        assert result["success"] is False
        assert "authentication failed" in result["error"].lower()

    def test_missing_api_key_fails(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {"base_url": "https://demo.symphonysummit.com", "api_key": ""},
        )
        service = integration_service_factory.get_service(None, d)
        result = service._test_integration()
        assert result["success"] is False
        assert "api key" in result["error"].lower()

    def test_inject_proxy_details(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "stored-key",
            },
        )
        service = integration_service_factory.get_service(None, d)
        body = service._inject_proxy_details(
            {
                "ServiceName": "IM_GetIncidentDetailsAndChangeHistory",
                "objCommonParameters": {"TicketNo": 123},
            }
        )
        proxy = body["objCommonParameters"]["_ProxyDetails"]
        assert proxy["APIKey"] == "stored-key"
        assert proxy["ProxyID"] == 0
        assert body["objCommonParameters"]["TicketNo"] == 123

    def test_inject_proxy_details_org_override(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "stored-key",
            },
        )
        service = integration_service_factory.get_service(None, d)
        body = service._inject_proxy_details(
            {
                "ServiceName": "SR_GetServiceCatalogDetails",
                "objCommonParameters": {
                    "_ProxyDetails": {"OrgID": 5},
                },
            }
        )
        assert body["objCommonParameters"]["_ProxyDetails"]["OrgID"] == 5

    def test_forms_structure(self):
        form = SymphonySummitService.get_forms()
        field_names = [c["name"] for c in form["children"]]
        assert field_names == ["base_url", "api_key"]

    def test_supported_interfaces(self):
        interfaces = SymphonySummitService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_sensitive_field_excluded(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "super-secret",
            },
        )
        integration = SymphonySummitIntegration(**d)
        dumped = integration.model_dump()
        assert "api_key" not in dumped

    def test_rest_api_creds(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "key",
            },
        )
        service = integration_service_factory.get_service(None, d)
        creds = service.generate_rest_api_creds()
        assert creds.base_url.endswith("CommonWS_JsonObjCall")
        assert creds.headers.get("Content-Type") == "application/json"
        assert creds.headers.get("Accept") == "application/json"
        assert creds.envs["SYMPHONY_SUMMIT_API_KEY"] == "key"
        assert creds.envs["SYMPHONY_SUMMIT_BASE_URL"] == "https://demo.symphonysummit.com"
        assert creds.envs["SYMPHONY_SUMMIT_PROXY_ID"] == DEFAULT_PROXY_ID
        assert creds.envs["SYMPHONY_SUMMIT_ORG_ID"] == DEFAULT_ORG_ID

    def test_inject_proxy_details_uses_creds_envs(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": "https://demo.symphonysummit.com",
                "api_key": "from-integration",
            },
        )
        service = integration_service_factory.get_service(None, d)
        creds = service.generate_rest_api_creds()
        creds.envs["SYMPHONY_SUMMIT_API_KEY"] = "from-creds"
        body = service._inject_proxy_details(
            {"ServiceName": "IM_GetIncidentDetailsAndChangeHistory"},
            envs=creds.envs,
        )
        assert (
            body["objCommonParameters"]["_ProxyDetails"]["APIKey"] == "from-creds"
        )

    def test_actions_generation(self):
        actions = SymphonySummitService.get_all_rest_api_actions()
        assert len(actions) == EXPECTED_ACTION_COUNT
        for action in actions:
            assert action.name and action.name.strip()
            assert action.integration_type == "symphony_summit"
            assert action.code.startswith("{base_url}")
            assert "action=" in action.code
            param_names = [p.name for p in action.parameters_definition]
            assert "method" in param_names
            assert "body" in param_names
            body_param = next(
                p for p in action.parameters_definition if p.name == "body"
            )
            assert body_param.values.get("ServiceName") in EXPECTED_SERVICE_NAMES

        action_names_lower = " ".join(a.name.lower() for a in actions)
        assert "catalog" in action_names_lower
        assert "incident" in action_names_lower
        assert "service request" in action_names_lower
        assert "list" in action_names_lower
        assert "change" in action_names_lower

    def test_open_api_spec_structure(self):
        from autobotAI_integrations.integrations import symphony_summit

        spec_path = Path(symphony_summit.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))

        assert spec["servers"][0]["url"] == "{base_url}"
        assert len(spec["paths"]) == EXPECTED_ACTION_COUNT
        service_names = {
            op["requestBody"]["content"]["application/json"]["schema"]["example"][
                "ServiceName"
            ]
            for path_item in spec["paths"].values()
            for op in path_item.values()
            if isinstance(op, dict) and "requestBody" in op
        }
        assert service_names == EXPECTED_SERVICE_NAMES

    def test_action_tasks_build_with_dummy_creds(
        self, dummy_symphony_summit, sample_restapi_task
    ):
        service = integration_service_factory.get_service(None, dummy_symphony_summit)
        creds = service.generate_rest_api_creds()
        assert creds.envs["SYMPHONY_SUMMIT_API_KEY"] == DUMMY_TOKENS["api_key"]

        for action in service.get_all_rest_api_actions():
            task = sample_restapi_task(
                dummy_symphony_summit, action.code, action.parameters_definition
            )
            assert task.creds.base_url.endswith("CommonWS_JsonObjCall")
            assert task.connection_interface == ConnectionInterfaces.REST_API
            assert task.executable == action.code

    def test_dummy_creds_action_run_injects_proxy(
        self, dummy_symphony_summit, sample_restapi_task, monkeypatch
    ):
        captured = {}

        def mock_request(**kwargs):
            captured.update(kwargs)
            response = requests.Response()
            response.status_code = 200
            response._content = b'{"Errors": ""}'
            response.headers["Content-Type"] = "application/json"
            return response

        monkeypatch.setattr(requests, "request", mock_request)

        service = integration_service_factory.get_service(None, dummy_symphony_summit)
        action = next(
            a
            for a in service.get_all_rest_api_actions()
            if "Get incident details" in a.name
        )
        task = sample_restapi_task(
            dummy_symphony_summit, action.code, action.parameters_definition
        )
        result = handle_task(task)

        assert captured["method"] == "POST"
        assert captured["url"].endswith("CommonWS_JsonObjCall/?action=IM_GetIncidentDetailsAndChangeHistory")
        proxy = captured["json"]["objCommonParameters"]["_ProxyDetails"]
        assert proxy["APIKey"] == DUMMY_TOKENS["api_key"]
        assert proxy["AuthType"] == "APIKEY"
        assert proxy["ProxyID"] == DEFAULT_PROXY_ID
        assert result.errors == []

    def test_dummy_creds_is_active_fails(self, dummy_symphony_summit):
        service = integration_service_factory.get_service(None, {
            **dummy_symphony_summit,
            "base_url": "https://invalid-nonexistent-summit-host.local",
        })
        result = service.is_active()
        assert not result["success"]
        assert "error" in result

    def test_get_details_preview(self):
        details = SymphonySummitService.get_details()
        assert details.get("preview") is True

    def test_invalid_base_url_rejected(self, sample_integration_dict):
        d = sample_integration_dict(
            "symphony_summit",
            {"base_url": "not-a-url", "api_key": "key"},
        )
        with pytest.raises(ValueError):
            SymphonySummitIntegration(**d)

    def test_live_connection(self, get_keys, sample_integration_dict):
        required = {
            "SYMPHONY_SUMMIT_BASE_URL",
            "SYMPHONY_SUMMIT_API_KEY",
        }
        if not required.issubset(get_keys):
            pytest.skip("Symphony Summit live keys not in .env")

        d = sample_integration_dict(
            "symphony_summit",
            {
                "base_url": get_keys["SYMPHONY_SUMMIT_BASE_URL"],
                "api_key": get_keys["SYMPHONY_SUMMIT_API_KEY"],
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service.is_active()
        assert result["success"], result.get("error")
