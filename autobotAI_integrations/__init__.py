"""autobotAI_integrations public API.

Thin package root: integration schemas and models load immediately; BaseService
and AIBaseService load only on first access (see ``autobotAI_integrations.base``).
"""
from autobotAI_integrations.integration_schema import (
    ConnectionTypes,
    IntegrationSchema,
    IntegrationStates,
)
from autobotAI_integrations.models import *  # noqa: F401,F403
from autobotAI_integrations.open_api_schema import MCPServerAction, OpenAPIAction
from autobotAI_integrations.payload_schema import Payload, Param, PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements

__all__ = [
    "AIBaseService",
    "BaseService",
    "ConnectionTypes",
    "IntegrationSchema",
    "IntegrationStates",
    "MCPServerAction",
    "OpenAPIAction",
    "Param",
    "Payload",
    "PayloadTask",
    "list_of_unique_elements",
]

_LAZY_ATTRS = frozenset({"BaseService", "AIBaseService"})


def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        from autobotAI_integrations import base

        return getattr(base, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(__all__))
