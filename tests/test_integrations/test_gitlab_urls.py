"""Credential-free unit tests for GitLab URL handling.

The other GitLab tests need a live GITLAB_TOKEN, so the self-managed base_url
bug they were meant to catch went unnoticed: REST creds only had `/api/v4`
appended when the URL started with "https://gitlab.com", so every self-managed
instance had its REST calls aimed at the web UI root instead of the API. That
returns HTML/404 and reaches the user as a generic "something went wrong" —
while the connection test still passed, because `_test_integration` uses
python-gitlab, which appends the API path itself.
"""
import pytest

from autobotAI_integrations.integrations.gitlab import GitlabService


def _svc(base_url):
    return GitlabService(
        {},
        {
            # BaseSchema requires these; they are irrelevant to URL handling.
            "userId": "u-1",
            "cspName": "gitlab",
            "alias": "gitlab-test",
            "base_url": base_url,
            "token": "tkn",
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
