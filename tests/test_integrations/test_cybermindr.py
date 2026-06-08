import json
import traceback
from pathlib import Path

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.cybermindr import (
    CyberMindrIntegration,
    CyberMindrService,
)
from autobotAI_integrations.models import ConnectionInterfaces


EXPECTED_CYBERMINDR_TAGS = {
    "Assets",
    "Findings",
    "Attack Paths",
    "Reports",
    "Remediations",
}


class TestClassCyberMindr:
    def test_factory_registration(self):
        cls = integration_service_factory.get_service_cls("cybermindr")
        assert cls is CyberMindrService

    def test_schema_and_forms(self, sample_integration_dict):
        integration_dict = sample_integration_dict(
            "cybermindr",
            {"api_key": "test-api-key", "base_url": "https://app.cybermindr.com"}
        )
        integration = CyberMindrIntegration(**integration_dict)
        assert integration.api_key == "test-api-key"
        assert integration.base_url == "https://app.cybermindr.com"
        assert integration.name == "CyberMindr"

        form = CyberMindrService.get_forms()
        assert form["label"] == "CyberMindr"
        
        base_url_field = next(c for c in form["children"] if c["name"] == "base_url")
        assert base_url_field["required"] is True
        assert base_url_field["type"] == "text"

        token_field = next(c for c in form["children"] if c["name"] == "api_key")
        assert token_field["required"] is True
        assert token_field["type"] == "text/password"

    def test_supported_interfaces(self):
        interfaces = CyberMindrService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_rest_api_creds(self, sample_integration_dict):
        integration_dict = sample_integration_dict(
            "cybermindr",
            {"api_key": "test-api-key", "base_url": "https://app.cybermindr.com"}
        )
        service = integration_service_factory.get_service(None, integration_dict)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://app.cybermindr.com"
        assert creds.headers.get("Authorization") == "Bearer test-api-key"

    def test_actions_generation(self):
        actions = CyberMindrService.get_all_rest_api_actions()
        assert len(actions) == 9, "expected 9 endpoints from the CyberMindr open_api.json"
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""

    def test_open_api_covers_all_surfaces(self):
        from autobotAI_integrations.integrations import cybermindr

        spec_path = Path(cybermindr.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        servers = spec["servers"]
        assert len(servers) > 0
        assert servers[0]["url"] == "{base_url}"

        tags_seen = {
            tag
            for path_item in spec["paths"].values()
            for op in path_item.values()
            if isinstance(op, dict)
            for tag in op.get("tags", [])
        }
        missing = EXPECTED_CYBERMINDR_TAGS - tags_seen
        assert not missing, f"open_api.json missing tags: {missing}"

        assert spec["components"]["securitySchemes"]["BearerAuth"] == {
            "type": "http",
            "scheme": "bearer",
            "description": "API key generated from CyberMindr dashboard: Settings -> API -> Generate New API Key. Pass as: Authorization: Bearer <api_key>"
        }

    def test_cybermindr_token(self, get_keys, sample_integration_dict):
        if "CYBERMINDR_API_KEY" not in get_keys or "CYBERMINDR_BASE_URL" not in get_keys:
            pytest.skip("CyberMindr live credentials are not configured")
        tokens = {
            "api_key": get_keys["CYBERMINDR_API_KEY"],
            "base_url": get_keys["CYBERMINDR_BASE_URL"]
        }
        integration = sample_integration_dict("cybermindr", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

        tokens = {
            "api_key": get_keys["CYBERMINDR_API_KEY"][:-3],
            "base_url": get_keys["CYBERMINDR_BASE_URL"]
        }
        integration = sample_integration_dict("cybermindr", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_run(self, get_keys, sample_restapi_task, sample_integration_dict):
        if "CYBERMINDR_API_KEY" not in get_keys or "CYBERMINDR_BASE_URL" not in get_keys:
            pytest.skip("CyberMindr live credentials are not configured")
        tokens = {
            "api_key": get_keys["CYBERMINDR_API_KEY"],
            "base_url": get_keys["CYBERMINDR_BASE_URL"]
        }
        integration = sample_integration_dict("cybermindr", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            try:
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
            except Exception:
                traceback.print_exc()
                raise
