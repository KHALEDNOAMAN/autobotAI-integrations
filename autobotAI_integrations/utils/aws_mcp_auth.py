"""
AWS MCP Server authentication helpers.

The official AWS MCP Server (https://aws-mcp.{region}.api.aws/mcp) requires
IAM SigV4 signing on HTTP requests. These helpers build MCPCreds and sign
requests without putting long-lived secrets in HTTP header maps when IAM
fields are used instead.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

from autobotAI_integrations.models import MCPCreds

AWS_MCP_SIGV4_SERVICE = "aws-mcp"

AWS_MCP_ENDPOINTS = {
    "us-east-1": "https://aws-mcp.us-east-1.api.aws/mcp",
    "eu-central-1": "https://aws-mcp.eu-central-1.api.aws/mcp",
}


def resolve_aws_mcp_url(region: str) -> str:
    url = AWS_MCP_ENDPOINTS.get(region)
    if not url:
        supported = ", ".join(sorted(AWS_MCP_ENDPOINTS))
        raise ValueError(
            f"Unsupported AWS MCP endpoint region {region!r}; use one of: {supported}"
        )
    return url


def is_aws_mcp_url(url: str) -> bool:
    """Return True when *url* targets the managed AWS MCP Server over HTTPS."""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return False
    host = (parsed.hostname or "").lower()
    return host.startswith("aws-mcp.") and host.endswith(".api.aws")


def aws_mcp_endpoint_region(url: str) -> Optional[str]:
    """Extract signing region from a managed AWS MCP URL."""
    if not is_aws_mcp_url(url):
        return None
    host = urlparse(url).hostname or ""
    match = re.match(r"aws-mcp\.([a-z0-9-]+)\.api\.aws", host)
    return match.group(1) if match else None


def build_aws_mcp_creds(
    *,
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    sigv4_region: Optional[str] = None,
    default_aws_region: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> MCPCreds:
    """Build MCPCreds for AWS MCP Server using IAM fields (not secrets in headers)."""
    headers = dict(extra_headers or {})
    if default_aws_region:
        headers.setdefault("x-aws-mcp-default-region", default_aws_region)

    return MCPCreds(
        headers=headers,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
        aws_sigv4_region=sigv4_region,
        aws_sigv4_service=AWS_MCP_SIGV4_SERVICE,
        aws_default_region=default_aws_region,
    )


def sign_aws_mcp_http_request(
    *,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    body: bytes = b"",
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    sigv4_region: Optional[str] = None,
    sigv4_service: str = AWS_MCP_SIGV4_SERVICE,
) -> Dict[str, str]:
    """Return SigV4-signed HTTP headers for a single AWS MCP Server request."""
    region = sigv4_region or aws_mcp_endpoint_region(url)
    if not region:
        raise ValueError(f"Cannot determine SigV4 region for AWS MCP URL: {url}")

    creds = Credentials(access_key_id, secret_access_key, session_token)
    request = AWSRequest(
        method=method.upper(),
        url=url,
        data=body if body else None,
        headers=dict(headers or {}),
    )
    SigV4Auth(creds, sigv4_service, region).add_auth(request)
    return dict(request.headers)


def mcp_remote_server_aws_fields(
    creds: MCPCreds,
    *,
    mcp_url: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Extract AWS IAM fields for MCPRemoteServer; signing region comes from *mcp_url*."""
    if not creds.aws_access_key_id or not creds.aws_secret_access_key:
        return {}

    sigv4_region = (
        aws_mcp_endpoint_region(mcp_url)
        if mcp_url and is_aws_mcp_url(mcp_url)
        else creds.aws_sigv4_region
    )
    return {
        "aws_access_key_id": creds.aws_access_key_id,
        "aws_secret_access_key": creds.aws_secret_access_key,
        "aws_session_token": creds.aws_session_token,
        "aws_sigv4_region": sigv4_region,
        "aws_sigv4_service": creds.aws_sigv4_service or AWS_MCP_SIGV4_SERVICE,
        "aws_default_region": creds.aws_default_region,
    }


def build_aws_mcp_sigv4_httpx_auth(
    *,
    mcp_url: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    default_aws_region: Optional[str] = None,
) -> Tuple[Dict[str, str], object]:
    """
    Return ``(headers, httpx.Auth)`` for pydantic-ai MCPToolset (local testing only).

    Use ``headers`` + ``auth`` — not ``http_client`` — with fastmcp HTTP transports.
    """
    import httpx

    region = aws_mcp_endpoint_region(mcp_url)
    if not region:
        raise ValueError(f"Cannot determine SigV4 region for AWS MCP URL: {mcp_url}")

    creds = build_aws_mcp_creds(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
        sigv4_region=region,
        default_aws_region=default_aws_region,
    )
    sigv4_service = creds.aws_sigv4_service or AWS_MCP_SIGV4_SERVICE

    class _AWSMCPSigV4Auth(httpx.Auth):
        def auth_flow(self, request):
            body = request.content if request.content is not None else b""
            for name in ("authorization", "x-amz-date", "x-amz-security-token"):
                if name in request.headers:
                    del request.headers[name]
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
                sigv4_region=region,
                sigv4_service=sigv4_service,
            )
            request.headers.update(signed_headers)
            yield request

    return dict(creds.headers), _AWSMCPSigV4Auth()
