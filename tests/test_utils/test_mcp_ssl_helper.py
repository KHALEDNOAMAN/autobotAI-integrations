from types import SimpleNamespace

from autobotAI_integrations.models import MCPCreds
from autobotAI_integrations.utils.mcp_ssl_helper import resolve_mcp_ignore_ssl


def test_default_is_verify_tls():
    assert resolve_mcp_ignore_ssl() is False
    assert resolve_mcp_ignore_ssl(SimpleNamespace()) is False


def test_ignore_ssl_field():
    assert resolve_mcp_ignore_ssl({"ignore_ssl": True}) is True
    assert resolve_mcp_ignore_ssl({"ignore_ssl": False}) is False


def test_verify_ssl_field_inverted():
    assert resolve_mcp_ignore_ssl({"verify_ssl": False}) is True
    assert resolve_mcp_ignore_ssl({"verify_ssl": True}) is False


def test_verify_cert_field_inverted():
    assert resolve_mcp_ignore_ssl({"verify_cert": False}) is True
    assert resolve_mcp_ignore_ssl({"verify_cert": True}) is False


def test_creds_ignore_ssl_wins():
    assert (
        resolve_mcp_ignore_ssl(
            {"ignore_ssl": False},
            MCPCreds(ignore_ssl=True),
        )
        is True
    )
