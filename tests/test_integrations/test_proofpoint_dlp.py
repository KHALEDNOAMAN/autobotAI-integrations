import pytest
import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.proofpoint_dlp import (
    ProofpointDLPIntegration,
    ProofpointDLPService,
)
from autobotAI_integrations.models import ConnectionInterfaces


class TestProofpointDLP:

    def test_factory_registration(self):
        """The factory must auto-discover ProofpointDLPService."""
        cls = integration_service_factory.get_service_cls("proofpoint_dlp")
        assert cls is ProofpointDLPService

    def test_schema_defaults(self, sample_integration_dict):
        """Schema must have correct name, category, and region default."""
        integration_dict = sample_integration_dict(
            "proofpoint_dlp",
            {
                "api_token": "test-token",
                "subdomain": "myco",
                "region": "us",
            },
        )
        integration = ProofpointDLPIntegration(**integration_dict)
        assert integration.name == "Proofpoint DLP"
        assert integration.category == "security_tools"
        assert integration.region == "us"
        assert integration.subdomain == "myco"

    def test_base_url_us(self, sample_integration_dict):
        """US region must produce tessian-app.com URL."""
        d = sample_integration_dict(
            "proofpoint_dlp",
            {"api_token": "tok", "subdomain": "myco", "region": "us"},
        )
        integration = ProofpointDLPIntegration(**d)
        assert integration.base_url == "https://myco.tessian-app.com"

    def test_base_url_eu(self, sample_integration_dict):
        """EU region must produce tessian-platform.com URL."""
        d = sample_integration_dict(
            "proofpoint_dlp",
            {"api_token": "tok", "subdomain": "myco", "region": "eu"},
        )
        integration = ProofpointDLPIntegration(**d)
        assert integration.base_url == "https://myco.tessian-platform.com"

    def test_forms_structure(self):
        """get_forms() must return all required fields."""
        form = ProofpointDLPService.get_forms()
        assert form["label"] == "Proofpoint DLP"
        assert form["type"] == "form"
        field_names = [c["name"] for c in form["children"]]
        assert "subdomain" in field_names
        assert "region" in field_names
        assert "api_token" in field_names
        assert "skip_test" in field_names

    def test_supported_interfaces(self):
        """Only REST_API must be in supported interfaces."""
        interfaces = ProofpointDLPService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_sensitive_field_excluded(self, sample_integration_dict):
        """api_token must NOT appear in model_dump() output."""
        d = sample_integration_dict(
            "proofpoint_dlp",
            {"api_token": "super-secret-token", "subdomain": "myco"},
        )
        integration = ProofpointDLPIntegration(**d)
        dumped = integration.model_dump()
        assert "api_token" not in dumped, "api_token must be excluded from serialisation"

    def test_rest_api_creds(self, sample_integration_dict):
        """generate_rest_api_creds() must set correct base_url and Authorization header."""
        d = sample_integration_dict(
            "proofpoint_dlp",
            {"api_token": "my-token", "subdomain": "myco", "region": "us"},
        )
        service = integration_service_factory.get_service(None, d)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://myco.tessian-app.com"
        assert creds.headers.get("Authorization") == "API-Token my-token"

    def test_actions_generation(self):
        """open_api.json must produce at least one action per tag."""
        actions = ProofpointDLPService.get_all_rest_api_actions()
        assert len(actions) > 0, "Expected REST API actions from open_api.json"
        for action in actions:
            assert action.name and action.name.strip(), "Each action must have a name"
        # Verify all expected tags are covered
        action_names_lower = " ".join(a.name.lower() for a in actions)
        assert "event" in action_names_lower
        assert "group" in action_names_lower
        assert "user" in action_names_lower
        assert "audit" in action_names_lower

    def test_skip_test_bypasses_connectivity(self, sample_integration_dict):
        """skip_test=True must return success without making any HTTP call."""
        d = sample_integration_dict(
            "proofpoint_dlp",
            {
                "api_token": "fake",
                "subdomain": "nonexistent",
                "region": "us",
                "skip_test": True,
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service._test_integration()
        assert result["success"] is True

    # ------------------------------------------------------------------ #
    # Live tests — only run when .env keys are set                         #
    # ------------------------------------------------------------------ #

    def test_live_connection(self, get_keys, sample_integration_dict):
        """Verify real credentials connect successfully."""
        required = {
            "PROOFPOINT_DLP_API_TOKEN",
            "PROOFPOINT_DLP_SUBDOMAIN",
        }
        if not required.issubset(get_keys):
            pytest.skip("Proofpoint DLP live keys not in .env — skipping live test")

        d = sample_integration_dict(
            "proofpoint_dlp",
            {
                "api_token": get_keys["PROOFPOINT_DLP_API_TOKEN"],
                "subdomain": get_keys["PROOFPOINT_DLP_SUBDOMAIN"],
                "region": get_keys.get("PROOFPOINT_DLP_REGION", "us"),
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service.is_active()
        print(result)
        assert result["success"], result.get("error")

    def test_live_invalid_token(self, get_keys, sample_integration_dict):
        """Invalid token must return success=False."""
        required = {"PROOFPOINT_DLP_SUBDOMAIN"}
        if not required.issubset(get_keys):
            pytest.skip("PROOFPOINT_DLP_SUBDOMAIN not in .env — skipping")

        d = sample_integration_dict(
            "proofpoint_dlp",
            {
                "api_token": "invalid-token-xyz",
                "subdomain": get_keys["PROOFPOINT_DLP_SUBDOMAIN"],
                "region": get_keys.get("PROOFPOINT_DLP_REGION", "us"),
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service.is_active()
        print(result)
        assert not result["success"]

    def test_live_actions_run(
        self, get_keys, sample_restapi_task, sample_integration_dict
    ):
        """Run each REST action against live Proofpoint; log any errors."""
        required = {
            "PROOFPOINT_DLP_API_TOKEN",
            "PROOFPOINT_DLP_SUBDOMAIN",
        }
        if not required.issubset(get_keys):
            pytest.skip("Proofpoint DLP live keys not in .env — skipping")

        d = sample_integration_dict(
            "proofpoint_dlp",
            {
                "api_token": get_keys["PROOFPOINT_DLP_API_TOKEN"],
                "subdomain": get_keys["PROOFPOINT_DLP_SUBDOMAIN"],
                "region": get_keys.get("PROOFPOINT_DLP_REGION", "us"),
            },
        )
        service = integration_service_factory.get_service(None, d)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            try:
                task = sample_restapi_task(
                    d, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
            except Exception:
                traceback.print_exc()
