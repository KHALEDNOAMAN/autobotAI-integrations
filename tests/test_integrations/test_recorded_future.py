import json
import traceback
from pathlib import Path

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.recorded_future import (
    RECORDED_FUTURE_BASE_URL,
    RecordedFutureIntegration,
    RecordedFutureService,
)
from autobotAI_integrations.models import ConnectionInterfaces


# All Recorded Future API surfaces declared via tags in open_api.json.
EXPECTED_RF_TAGS = {
    "Connect",
    "Identity",
    "Detection Rule",
    "Detection Rule Relation",
    "Entity Match",
    "Links",
    "List",
    "Playbook Alert",
    "Threat",
    "Malware Intelligence",
    "Analyst Note",
    "Risk History",
    "Fusion",
    "SOAR",
    "Alert",
    "Collective Insights",
}


class TestClassRecordedFuture:
    def test_factory_registration(self):
        cls = integration_service_factory.get_service_cls("recorded_future")
        assert cls is RecordedFutureService

    def test_schema_and_forms(self, sample_integration_dict):
        integration_dict = sample_integration_dict(
            "recorded_future", {"api_token": "rf-test"}
        )
        integration = RecordedFutureIntegration(**integration_dict)
        assert integration.api_token == "rf-test"
        assert integration.name == "Recorded Future"

        form = RecordedFutureService.get_forms()
        assert form["label"] == "Recorded Future"
        token_field = next(c for c in form["children"] if c["name"] == "api_token")
        assert token_field["required"] is True
        assert token_field["type"] == "text/password"

    def test_supported_interfaces(self):
        interfaces = RecordedFutureService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_rest_api_creds(self, sample_integration_dict):
        integration = sample_integration_dict(
            "recorded_future", {"api_token": "rf-test"}
        )
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == RECORDED_FUTURE_BASE_URL
        # RF uses X-RFToken, not Authorization Bearer.
        assert creds.headers.get("X-RFToken") == "rf-test"
        assert "Authorization" not in creds.headers

    def test_actions_generation(self):
        actions = RecordedFutureService.get_all_rest_api_actions()
        assert len(actions) > 30, "expected the full RF surface"
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""

    def test_open_api_covers_all_surfaces(self):
        from autobotAI_integrations.integrations import recorded_future

        spec_path = Path(recorded_future.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        servers = spec["servers"]
        assert any(s["url"] == RECORDED_FUTURE_BASE_URL for s in servers)

        tags_seen = {
            tag
            for path_item in spec["paths"].values()
            for op in path_item.values()
            if isinstance(op, dict)
            for tag in op.get("tags", [])
        }
        missing = EXPECTED_RF_TAGS - tags_seen
        assert not missing, f"open_api.json missing tags: {missing}"

        # Auth scheme matches the X-RFToken header used in generate_rest_api_creds.
        assert spec["components"]["securitySchemes"]["RFTokenAuth"] == {
            "type": "apiKey",
            "in": "header",
            "name": "X-RFToken",
        }

    def test_recorded_future_token(self, get_keys, sample_integration_dict):
        if "RECORDED_FUTURE_API_TOKEN" not in get_keys:
            return
        tokens = {"api_token": get_keys["RECORDED_FUTURE_API_TOKEN"]}
        integration = sample_integration_dict("recorded_future", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {"api_token": get_keys["RECORDED_FUTURE_API_TOKEN"][:-3]}
        integration = sample_integration_dict("recorded_future", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_run(self, get_keys, sample_restapi_task, sample_integration_dict):
        if "RECORDED_FUTURE_API_TOKEN" not in get_keys:
            return
        tokens = {"api_token": get_keys["RECORDED_FUTURE_API_TOKEN"]}
        integration = sample_integration_dict("recorded_future", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            try:
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
            except Exception:
                traceback.print_exc()
