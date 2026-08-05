"""Credential-free unit tests for GitLab URL handling.

The other GitLab tests need a live GITLAB_TOKEN, so the self-managed base_url
bug they were meant to catch went unnoticed: REST creds only had `/api/v4`
appended when the URL started with "https://gitlab.com", so every self-managed
instance had its REST calls aimed at the web UI root instead of the API. That
returns HTML/404 and reaches the user as a generic "something went wrong" —
while the connection test still passed, because `_test_integration` uses
python-gitlab, which appends the API path itself.
"""
from unittest.mock import MagicMock

import pytest

from autobotAI_integrations.integrations.gitlab import GitlabService


def _svc(base_url, **extra):
    return GitlabService(
        {},
        {
            # BaseSchema requires these; they are irrelevant to URL handling.
            "userId": "u-1",
            "cspName": "gitlab",
            "alias": "gitlab-test",
            "base_url": base_url,
            "token": "tkn",
            **extra,
        },
    )


class TestRestApiBaseUrl:
    @pytest.mark.parametrize(
        "base_url,expected",
        [
            # gitlab.com — unchanged from the previous behaviour.
            ("https://gitlab.com/", "https://gitlab.com/api/v4"),
            ("https://gitlab.com", "https://gitlab.com/api/v4"),
            # Self-managed: these are the ones that were broken.
            ("https://gitlab.acme.com/", "https://gitlab.acme.com/api/v4"),
            ("https://git.acme.com/", "https://git.acme.com/api/v4"),
            ("https://gitlab.internal.acme.io", "https://gitlab.internal.acme.io/api/v4"),
            ("http://gitlab.acme.com", "http://gitlab.acme.com/api/v4"),
            # The old prefix match caught this one by accident; keep it working.
            ("https://gitlab.company.com/", "https://gitlab.company.com/api/v4"),
        ],
    )
    def test_api_path_is_appended_for_every_host(self, base_url, expected):
        assert _svc(base_url).generate_rest_api_creds().base_url == expected

    @pytest.mark.parametrize(
        "base_url",
        [
            "https://git.acme.com/api/v4",
            "https://git.acme.com/api/v4/",
            "https://gitlab.com/api/v4",
        ],
    )
    def test_existing_api_path_is_not_doubled(self, base_url):
        creds = _svc(base_url).generate_rest_api_creds()
        assert creds.base_url.count("/api/v") == 1
        assert creds.base_url.endswith("/api/v4")

    def test_token_travels_as_private_token_header(self):
        assert _svc("https://git.acme.com").generate_rest_api_creds().headers == {
            "PRIVATE-TOKEN": "tkn"
        }


class TestMcpHostRestriction:
    """MCP stays restricted to gitlab.com — but must say why.

    mcp_servers.json is loaded by get_all_mcp_server_actions(), a classmethod
    with no access to the instance, so its URLs are hardcoded to
    https://gitlab.com/api/v4/mcp. Allowing a self-managed integration through
    would send that customer's private token to gitlab.com.
    """

    def test_public_gitlab_gets_bearer_creds(self):
        creds = _svc("https://gitlab.com/").generate_mcp_creds()
        assert creds.headers["Authorization"] == "Bearer tkn"

    @pytest.mark.parametrize(
        "base_url",
        [
            "https://gitlab.acme.com/",
            "https://git.acme.com/",
            # Not https — must not be treated as public gitlab.com.
            "http://gitlab.com/",
            # Look-alike host that a prefix match would wrongly accept.
            "https://gitlab.com.evil.example/",
            "",
        ],
    )
    def test_non_public_hosts_are_refused(self, base_url):
        with pytest.raises(ValueError) as exc:
            _svc(base_url).generate_mcp_creds()
        message = str(exc.value)
        # Must name the offending host and the reason, not be generic — a bare
        # Exception here is what reached users as "something went wrong".
        assert "gitlab.com" in message
        assert "Self-managed" in message

    def test_refusal_does_not_block_the_other_interfaces(self):
        """A self-managed host must still work for REST; only MCP is limited."""
        svc = _svc("https://git.acme.com/")
        assert svc.generate_rest_api_creds().base_url.endswith("/api/v4")
        with pytest.raises(ValueError):
            svc.generate_mcp_creds()


class TestVerifySsl:
    """Self-managed GitLab is often behind a private CA or self-signed cert."""

    def test_defaults_to_verifying(self):
        """Opt-out, not opt-in — gitlab.com users must not silently lose TLS
        verification just because the field was added."""
        svc = _svc("https://gitlab.com/")
        assert svc.integration.verify_ssl is True
        assert svc.generate_rest_api_creds().verify_ssl is True
        assert svc.generate_python_sdk_creds().envs["GITLAB_VERIFY_SSL"] == "True"

    def test_disabling_reaches_rest_creds(self):
        creds = _svc("https://git.acme.com/", verify_ssl=False).generate_rest_api_creds()
        assert creds.verify_ssl is False

    def test_disabling_reaches_sdk_envs(self):
        envs = _svc("https://git.acme.com/", verify_ssl=False).generate_python_sdk_creds().envs
        assert envs["GITLAB_VERIFY_SSL"] == "False"

    def test_the_form_exposes_the_checkbox(self):
        fields = {c["name"]: c for c in GitlabService.get_forms()["children"]}
        assert fields["verify_ssl"]["type"] == "checkbox"
        assert fields["verify_ssl"]["default"] is True

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("True", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("no", False),
            ("", False),
            (None, True),  # key absent entirely — payloads built before this field
        ],
    )
    def test_sdk_client_receives_a_real_bool(self, env_value, expected, monkeypatch):
        """envs cross the wire as strings, so "False" must not read as truthy.

        Drives the real build_python_exec_combinations_hook and captures what
        python-gitlab would actually have been constructed with.
        """
        captured = {}

        class _FakeGitlabModule:
            @staticmethod
            def Gitlab(url, private_token=None, ssl_verify=None):
                captured["url"] = url
                captured["ssl_verify"] = ssl_verify
                return object()

        monkeypatch.setattr(
            "importlib.import_module", lambda *a, **k: _FakeGitlabModule
        )

        envs = {"GITLAB_ADDR": "https://git.acme.com", "GITLAB_TOKEN": "tkn"}
        if env_value is not None:
            envs["GITLAB_VERIFY_SSL"] = env_value

        task = MagicMock()
        task.creds.envs = envs
        task.params = []

        client_def = MagicMock()
        client_def.import_library_names = ["gitlab"]

        _svc("https://git.acme.com/").build_python_exec_combinations_hook(
            task, [client_def]
        )

        assert captured["ssl_verify"] is expected


def test_suite_is_running_against_the_working_tree():
    """Guard against silently testing an installed copy.

    A non-editable autobotAI_integrations can sit in site-packages (the core
    venv has one). If sys.path resolves to that instead of the checkout, every
    assertion above would be validating the shipped package, not the change.
    """
    import inspect
    from pathlib import Path

    import autobotAI_integrations

    loaded = Path(inspect.getfile(autobotAI_integrations)).resolve()
    repo = Path(__file__).resolve().parents[2] / "autobotAI_integrations"
    assert repo in loaded.parents or loaded.parent == repo, (
        f"tests are importing {loaded}, not the checkout at {repo}"
    )
