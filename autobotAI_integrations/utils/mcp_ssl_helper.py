"""Normalize integration SSL flags for MCP clients."""

from __future__ import annotations

from typing import Any


def resolve_mcp_ignore_ssl(
    integration: Any = None, creds: Any = None
) -> bool:
    """Return whether MCP should skip TLS verification.

    Default is False (verify TLS). Supports the field names used across
    integrations without requiring each ``generate_mcp_creds`` to set it:

    - ``ignore_ssl`` (GitLab, generic_rest_api, …)
    - ``verify_ssl`` (Acunetix, Nessus, RestAPICreds) → inverted
    - ``verify_cert`` (OpenSearch, MISP) → inverted

    Explicit ``MCPCreds.ignore_ssl`` wins when True.
    """
    if bool(getattr(creds, "ignore_ssl", False)):
        return True
    return _ignore_ssl_from_integration(integration)


def _ignore_ssl_from_integration(integration: Any) -> bool:
    if integration is None:
        return False

    if isinstance(integration, dict):
        if "ignore_ssl" in integration:
            return bool(integration.get("ignore_ssl"))
        if "verify_ssl" in integration:
            return not bool(integration.get("verify_ssl"))
        if "verify_cert" in integration:
            return not bool(integration.get("verify_cert"))
        return False

    fields = getattr(type(integration), "model_fields", None)
    if isinstance(fields, dict):
        if "ignore_ssl" in fields:
            return bool(getattr(integration, "ignore_ssl", False))
        if "verify_ssl" in fields:
            return not bool(getattr(integration, "verify_ssl", True))
        if "verify_cert" in fields:
            return not bool(getattr(integration, "verify_cert", True))
        return False

    if hasattr(integration, "ignore_ssl"):
        return bool(getattr(integration, "ignore_ssl"))
    if hasattr(integration, "verify_ssl"):
        return not bool(getattr(integration, "verify_ssl"))
    if hasattr(integration, "verify_cert"):
        return not bool(getattr(integration, "verify_cert"))
    return False
