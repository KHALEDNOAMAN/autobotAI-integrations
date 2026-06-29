"""
Connect to the managed AWS MCP Server and list runtime tools (``tools/list``).

Used by the dev CLI ``tests/test_integrations/_list_aws_mcp_tools.py`` and
available for future platform tooling. Requires the ``mcp`` and ``httpx``
packages (``pip install mcp httpx``).
"""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from autobotAI_integrations.utils.aws_mcp_auth import (
    AWS_MCP_ENDPOINTS,
    AWS_MCP_SIGV4_SERVICE,
    aws_mcp_endpoint_region,
    build_aws_mcp_creds,
    is_aws_mcp_url,
    sign_aws_mcp_http_request,
)

def tool_to_dict(tool: Any) -> Dict[str, Any]:
    """Normalise an MCP ``Tool`` object to a JSON-serialisable dict."""
    input_schema = getattr(tool, "inputSchema", None)
    if input_schema is not None and hasattr(input_schema, "model_dump"):
        input_schema = input_schema.model_dump()
    return {
        "name": getattr(tool, "name", ""),
        "description": getattr(tool, "description", "") or "",
        "input_schema": input_schema,
    }

def resolve_aws_mcp_url(region: str) -> str:
    """Return the managed AWS MCP URL for *region* (e.g. ``us-east-1``)."""
    url = AWS_MCP_ENDPOINTS.get(region)
    if not url:
        supported = ", ".join(sorted(AWS_MCP_ENDPOINTS))
        raise ValueError(
            f"Unsupported AWS MCP endpoint region {region!r}; use one of: {supported}"
        )
    return url

def _build_sigv4_httpx_client_factory(
    *,
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str],
    sigv4_region: str,
    sigv4_service: str,
    static_headers: Optional[Dict[str, str]] = None,
):
    import httpx

    class _AWSMCPSigV4Auth(httpx.Auth):
        def auth_flow(self, request):
            body = request.content if request.content is not None else b""
            signed_headers = sign_aws_mcp_http_request(
                method=request.method,
                url=str(request.url),
                headers={
                    k.decode(): v.decode()
                    for k, v in request.headers.raw
                    if k.decode().lower()
                    not in ("authorization", "x-amz-date", "x-amz-security-token")
                },
                body=body,
                access_key_id=access_key_id,
                secret_access_key=secret_access_key,
                session_token=session_token,
                sigv4_region=sigv4_region,
                sigv4_service=sigv4_service,
            )
            request.headers.update(signed_headers)
            yield request

    def _factory(headers=None, timeout=None, auth=None):
        client_headers = dict(static_headers or {})
        if headers:
            client_headers.update(headers)
        return httpx.AsyncClient(
            headers=client_headers,
            auth=_AWSMCPSigV4Auth(),
            timeout=timeout or httpx.Timeout(30.0),
        )

    return _factory

async def _open_aws_mcp_session(
    *,
    url: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    sigv4_region: Optional[str] = None,
    default_aws_region: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    connect_timeout: float = 15.0,
    init_timeout: float = 10.0,
):
    if not is_aws_mcp_url(url):
        raise ValueError(f"Not a managed AWS MCP URL: {url}")

    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError as exc:
        raise ImportError(
            "Missing MCP SDK. Install with: pip install mcp httpx"
        ) from exc

    region = sigv4_region or aws_mcp_endpoint_region(url)
    if not region:
        raise ValueError(f"Cannot determine SigV4 region for AWS MCP URL: {url}")

    creds = build_aws_mcp_creds(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        sigv4_region=region,
        default_aws_region=default_aws_region,
        extra_headers=extra_headers,
    )
    client_factory = _build_sigv4_httpx_client_factory(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        sigv4_region=region,
        sigv4_service=creds.aws_sigv4_service or AWS_MCP_SIGV4_SERVICE,
        static_headers=creds.headers,
    )

    stack = AsyncExitStack()
    try:
        try:
            transport = await asyncio.wait_for(
                stack.enter_async_context(
                    streamablehttp_client(
                        url=url,
                        httpx_client_factory=client_factory,
                    )
                ),
                timeout=connect_timeout,
            )
        except TypeError:
            transport = await asyncio.wait_for(
                stack.enter_async_context(streamablehttp_client(url=url)),
                timeout=connect_timeout,
            )

        session = await stack.enter_async_context(
            ClientSession(transport[0], transport[1])
        )
        await asyncio.wait_for(session.initialize(), timeout=init_timeout)
        return stack, session
    except Exception:
        await stack.aclose()
        raise

async def list_aws_mcp_tools(
    *,
    url: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    sigv4_region: Optional[str] = None,
    default_aws_region: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    connect_timeout: float = 15.0,
    init_timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Connect to *url*, call ``list_tools()``, and return tool metadata dicts.

    The caller does not need to manage the MCP session lifecycle; this function
    opens the connection, lists tools, and closes the session before returning.
    """
    stack, session = await _open_aws_mcp_session(
        url=url,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        sigv4_region=sigv4_region,
        default_aws_region=default_aws_region,
        extra_headers=extra_headers,
        connect_timeout=connect_timeout,
        init_timeout=init_timeout,
    )
    try:
        tools_result = await session.list_tools()
        mcp_tools = tools_result.tools if hasattr(tools_result, "tools") else []
        return [tool_to_dict(tool) for tool in mcp_tools]
    finally:
        await stack.aclose()
