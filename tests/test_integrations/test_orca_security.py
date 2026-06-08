"""
Tests for the Orca Security integration.

Offline tests (no credentials required):
  - Factory registration
  - Schema validation and field exclusion
  - Form structure and field definitions
  - Supported connection interfaces
  - REST API creds structure and auth header format
  - open_api.json structure — expected tags, server URL, security scheme
  - REST actions count and completeness
  - get_details() flags (compliance_supported, preview)
  - base_url validator (trailing slash strip, empty rejection)

Live tests (skip when env vars absent):
  - ORCA_API_TOKEN + ORCA_BASE_URL → is_active() returns True
  - Bad token → is_active() returns False
  - All REST actions execute without error
"""

import json
import traceback
from pathlib import Path

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.orca_security import (
    OrcaSecurityIntegration,
    OrcaSecurityService,
)
from autobotAI_integrations.models import ConnectionInterfaces

# All tags we expect to be present in open_api.json
EXPECTED_ORCA_TAGS = {"Alerts", "Assets", "Vulnerabilities", "Compliance"}

# All operationIds we expect — one per endpoint
EXPECTED_OPERATION_IDS = {
    "listAlerts",
    "getAlert",
    "updateAlert",
    "addAlertComment",
    "verifyAlert",
    "listAssets",
    "getAsset",
    "scanAsset",
    "listVulnerabilities",
    "getComplianceSummary",
}


class TestOrcaSecurityOffline:
    """All tests in this class run without live credentials."""

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    def test_factory_registration(self):
        """integration_service_factory must resolve 'orca_security' to OrcaSecurityService."""
        cls = integration_service_factory.get_service_cls("orca_security")
        assert cls is OrcaSecurityService

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def test_schema_instantiation(self, sample_integration_dict):
        """Schema must accept valid credentials and populate name/category correctly."""
        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": "test-token-abc123",
                "base_url": "https://app.orcasecurity.io",
            },
        )
        integration = OrcaSecurityIntegration(**d)
        assert integration.api_token == "test-token-abc123"
        assert integration.base_url == "https://app.orcasecurity.io"
        assert integration.name == "Orca Security"
        assert integration.category == "security_tools"

    def test_api_token_excluded_from_dump(self, sample_integration_dict):
        """api_token must never appear in model_dump() — it is marked exclude=True."""
        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": "super-secret-token",
                "base_url": "https://app.eu.orcasecurity.io",
            },
        )
        integration = OrcaSecurityIntegration(**d)
        dumped = integration.model_dump()
        assert "api_token" not in dumped, (
            "api_token must be excluded from model_dump() to prevent leaking to DB/logs"
        )

    def test_base_url_trailing_slash_stripped(self, sample_integration_dict):
        """Validator must strip trailing slashes from base_url."""
        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": "tok",
                "base_url": "https://app.orcasecurity.io/",
            },
        )
        integration = OrcaSecurityIntegration(**d)
        assert not integration.base_url.endswith("/")

    def test_base_url_empty_rejected(self, sample_integration_dict):
        """Validator must reject an empty base_url."""
        from pydantic import ValidationError

        d = sample_integration_dict(
            "orca_security",
            {"api_token": "tok", "base_url": ""},
        )
        with pytest.raises(ValidationError):
            OrcaSecurityIntegration(**d)

    # ------------------------------------------------------------------
    # Forms
    # ------------------------------------------------------------------
    def test_get_forms_structure(self):
        """get_forms() must return the expected label and two required fields."""
        form = OrcaSecurityService.get_forms()
        assert form["label"] == "Orca Security"
        assert form["type"] == "form"
        field_names = [f["name"] for f in form["children"]]
        assert "api_token" in field_names
        assert "base_url" in field_names

    def test_get_forms_api_token_field(self):
        """api_token field must be password type and required."""
        form = OrcaSecurityService.get_forms()
        token_field = next(f for f in form["children"] if f["name"] == "api_token")
        assert token_field["type"] == "text/password"
        assert token_field["required"] is True

    def test_get_forms_base_url_is_select_with_all_regions(self):
        """base_url field must be a select with all 5 Orca regions."""
        form = OrcaSecurityService.get_forms()
        url_field = next(f for f in form["children"] if f["name"] == "base_url")
        assert url_field["type"] == "select"
        assert url_field["required"] is True
        option_values = {o["value"] for o in url_field["options"]}
        expected_regions = {
            "https://app.orcasecurity.io",
            "https://app.eu.orcasecurity.io",
            "https://app.au.orcasecurity.io",
            "https://app.in.orcasecurity.io",
            "https://app.il.orcasecurity.io",
        }
        assert expected_regions == option_values, (
            f"Missing region options: {expected_regions - option_values}"
        )

    # ------------------------------------------------------------------
    # Interfaces & details
    # ------------------------------------------------------------------
    def test_supported_interfaces(self):
        """Must only expose REST_API — no Steampipe plugin exists for Orca."""
        interfaces = OrcaSecurityService.supported_connection_interfaces()
        assert interfaces == [ConnectionInterfaces.REST_API]

    def test_get_details_flags(self):
        """compliance_supported must be False and preview must be True."""
        details = OrcaSecurityService.get_details()
        assert details["compliance_supported"] is False, (
            "No compliance.json or Steampipe plugin — compliance_supported must be False"
        )
        assert details["preview"] is True
        assert details["supported_executor"] == "ecs"

    # ------------------------------------------------------------------
    # REST API creds
    # ------------------------------------------------------------------
    def test_generate_rest_api_creds_structure(self, sample_integration_dict):
        """generate_rest_api_creds() must return correct base_url and Token auth header."""
        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": "my-orca-token",
                "base_url": "https://app.eu.orcasecurity.io",
            },
        )
        service = integration_service_factory.get_service(None, d)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == "https://app.eu.orcasecurity.io"
        # Orca uses "Token <value>", NOT "Bearer <value>"
        assert creds.headers.get("Authorization") == "Token my-orca-token", (
            "Orca Security requires 'Token <value>' header, not Bearer"
        )
        assert creds.headers.get("Content-Type") == "application/json"

    def test_rest_api_creds_token_format(self, sample_integration_dict):
        """Auth header value must start with 'Token ' not 'Bearer '."""
        d = sample_integration_dict(
            "orca_security",
            {"api_token": "abc123", "base_url": "https://app.orcasecurity.io"},
        )
        service = integration_service_factory.get_service(None, d)
        creds = service.generate_rest_api_creds()
        auth = creds.headers.get("Authorization", "")
        assert auth.startswith("Token "), (
            f"Expected 'Token abc123' but got '{auth}'"
        )

    # ------------------------------------------------------------------
    # open_api.json spec
    # ------------------------------------------------------------------
    def test_open_api_file_exists(self):
        """open_api.json must exist in the integration folder."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        assert spec_path.exists(), "open_api.json not found in orca_security integration folder"

    def test_open_api_valid_json(self):
        """open_api.json must be valid JSON."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())
        assert spec["openapi"].startswith("3.")

    def test_open_api_server_url(self):
        """Server URL must use {base_url} template so region selection works."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())
        assert spec["servers"][0]["url"] == "{base_url}", (
            "Server URL must be '{base_url}' to support multi-region tenants"
        )

    def test_open_api_security_scheme_is_token(self):
        """Security scheme must use apiKey (Token) not Bearer."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())
        schemes = spec["components"]["securitySchemes"]
        assert "TokenAuth" in schemes
        token_scheme = schemes["TokenAuth"]
        assert token_scheme["type"] == "apiKey"
        assert token_scheme["in"] == "header"
        assert token_scheme["name"] == "Authorization"

    def test_open_api_covers_all_expected_tags(self):
        """open_api.json must have all expected top-level tags."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        tags_in_spec = {t["name"] for t in spec.get("tags", [])}
        missing = EXPECTED_ORCA_TAGS - tags_in_spec
        assert not missing, f"open_api.json missing top-level tags: {missing}"

    def test_open_api_all_operation_ids_present(self):
        """Every expected operationId must exist in the paths."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        found_ids = {
            op["operationId"]
            for path_item in spec["paths"].values()
            for op in path_item.values()
            if isinstance(op, dict) and "operationId" in op
        }
        missing = EXPECTED_OPERATION_IDS - found_ids
        assert not missing, f"Missing operationIds in open_api.json: {missing}"

    def test_open_api_write_operations_present(self):
        """Write operations (PUT alert, POST comment, POST verify, POST scan) must exist."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        write_ops = {
            op.get("operationId")
            for path_item in spec["paths"].values()
            for method, op in path_item.items()
            if method in ("put", "post", "patch") and isinstance(op, dict)
        }
        expected_writes = {"updateAlert", "addAlertComment", "verifyAlert", "scanAsset"}
        missing = expected_writes - write_ops
        assert not missing, f"Missing write operationIds: {missing}"

    # ------------------------------------------------------------------
    # Actions generation (parser round-trip)
    # ------------------------------------------------------------------
    def test_rest_actions_count(self):
        """Parser must produce exactly 10 actions from open_api.json."""
        actions = OrcaSecurityService.get_all_rest_api_actions()
        assert len(actions) == 10, (
            f"Expected 10 REST actions, got {len(actions)}: {[a.name for a in actions]}"
        )

    def test_rest_actions_have_names(self):
        """Every action must have a non-empty name."""
        actions = OrcaSecurityService.get_all_rest_api_actions()
        for action in actions:
            assert action.name and action.name.strip(), (
                f"Action with empty name found: {action}"
            )

    def test_rest_actions_cover_all_tags(self):
        """Actions must cover all 4 expected tags."""
        import autobotAI_integrations.integrations.orca_security as pkg
        spec_path = Path(pkg.__file__).parent / "open_api.json"
        spec = json.loads(spec_path.read_text())

        tags_in_paths = {
            tag
            for path_item in spec["paths"].values()
            for op in path_item.values()
            if isinstance(op, dict)
            for tag in op.get("tags", [])
        }
        missing = EXPECTED_ORCA_TAGS - tags_in_paths
        assert not missing, f"Tags missing from path operations: {missing}"

    # ------------------------------------------------------------------
    # Schema — get_schema()
    # ------------------------------------------------------------------
    def test_get_schema_returns_correct_class(self):
        """get_schema() must return OrcaSecurityIntegration."""
        assert OrcaSecurityService.get_schema() is OrcaSecurityIntegration

    # ------------------------------------------------------------------
    # Logo files
    # ------------------------------------------------------------------
    def test_logo_files_exist(self):
        """Both dark.svg and light.svg must exist in logo-img/."""
        import autobotAI_integrations.integrations.orca_security as pkg
        base = Path(pkg.__file__).parent / "logo-img"
        assert (base / "dark.svg").exists(), "logo-img/dark.svg missing"
        assert (base / "light.svg").exists(), "logo-img/light.svg missing"


# ----------------------------------------------------------------------
# Live tests — only run when env vars are set
# ----------------------------------------------------------------------
class TestOrcaSecurityLive:
    """
    Live connectivity tests. Skipped automatically when
    ORCA_API_TOKEN and ORCA_BASE_URL are not present in .env.
    """

    def test_valid_token_is_active(self, get_keys, sample_integration_dict):
        """A valid token + correct base_url must return success=True from is_active()."""
        if "ORCA_API_TOKEN" not in get_keys or "ORCA_BASE_URL" not in get_keys:
            pytest.skip("ORCA_API_TOKEN / ORCA_BASE_URL not configured in .env")

        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": get_keys["ORCA_API_TOKEN"],
                "base_url": get_keys["ORCA_BASE_URL"],
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service.is_active()
        assert result["success"] is True, (
            f"Expected success=True with valid token, got: {result}"
        )

    def test_invalid_token_is_inactive(self, get_keys, sample_integration_dict):
        """A corrupted token must return success=False from is_active()."""
        if "ORCA_API_TOKEN" not in get_keys or "ORCA_BASE_URL" not in get_keys:
            pytest.skip("ORCA_API_TOKEN / ORCA_BASE_URL not configured in .env")

        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": get_keys["ORCA_API_TOKEN"][:-4] + "XXXX",
                "base_url": get_keys["ORCA_BASE_URL"],
            },
        )
        service = integration_service_factory.get_service(None, d)
        result = service.is_active()
        assert result["success"] is False, (
            "Expected success=False with invalid token"
        )
        assert "error" in result

    def test_all_rest_actions_execute(
        self, get_keys, sample_restapi_task, sample_integration_dict
    ):
        """All 10 REST actions must execute without raising an exception."""
        if "ORCA_API_TOKEN" not in get_keys or "ORCA_BASE_URL" not in get_keys:
            pytest.skip("ORCA_API_TOKEN / ORCA_BASE_URL not configured in .env")

        d = sample_integration_dict(
            "orca_security",
            {
                "api_token": get_keys["ORCA_API_TOKEN"],
                "base_url": get_keys["ORCA_BASE_URL"],
            },
        )
        service = integration_service_factory.get_service(None, d)
        actions = service.get_all_rest_api_actions()

        for action in actions:
            try:
                task = sample_restapi_task(
                    d, action.code, action.parameters_definition
                )
                handle_task(task)
            except Exception:
                traceback.print_exc()
                raise
