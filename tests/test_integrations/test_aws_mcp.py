import pytest

from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.aws import AWSService
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.utils.aws_mcp_auth import (
    AWS_MCP_ENDPOINTS,
    aws_mcp_endpoint_region,
    is_aws_mcp_url,
    mcp_remote_server_aws_fields,
    resolve_aws_mcp_url,
    sign_aws_mcp_http_request,
)


class TestAWSMCPOnAWSIntegration:
    def test_supported_interfaces_includes_mcp_server(self):
        interfaces = AWSService.supported_connection_interfaces()
        assert ConnectionInterfaces.MCP_SERVER in interfaces
        assert ConnectionInterfaces.PYTHON_SDK in interfaces
        assert ConnectionInterfaces.STEAMPIPE in interfaces

    def test_mcp_catalog_actions(self):
        actions = AWSService.get_all_mcp_server_actions()
        assert len(actions) == 2
        names = {action.name for action in actions}
        assert "AWS MCP Server US East" in names
        assert "AWS MCP Server EU Frankfurt" in names
        urls = {action.code for action in actions}
        assert resolve_aws_mcp_url("us-east-1") in urls
        assert resolve_aws_mcp_url("eu-central-1") in urls
        for action in actions:
            assert action.integration_type == "aws"
            assert action.executable_type == "mcp_server"
            assert is_aws_mcp_url(action.code)

    def test_generate_mcp_creds_structure(self, get_keys, sample_integration_dict):
        integration = sample_integration_dict(
            "aws",
            {
                "access_key": get_keys["AWS_ACCESS_KEY_ID"],
                "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
                "session_token": get_keys.get("AWS_SESSION_TOKEN"),
                "activeRegions": [get_keys.get("AWS_REGION", "us-east-1")],
            },
        )
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_mcp_creds()
        assert creds.aws_access_key_id == get_keys["AWS_ACCESS_KEY_ID"]
        assert creds.aws_secret_access_key == get_keys["AWS_SECRET_ACCESS_KEY"]
        assert creds.aws_default_region == get_keys.get("AWS_REGION", "us-east-1")
        assert creds.aws_sigv4_region is None
        assert "Authorization" not in creds.headers

    def test_mcp_remote_server_aws_fields(self, get_keys, sample_integration_dict):
        integration = sample_integration_dict(
            "aws",
            {
                "access_key": get_keys["AWS_ACCESS_KEY_ID"],
                "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            },
        )
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_mcp_creds()
        fields = mcp_remote_server_aws_fields(creds)
        assert fields["aws_access_key_id"] == get_keys["AWS_ACCESS_KEY_ID"]
        assert fields.get("aws_sigv4_region") is None

        frankfurt_fields = mcp_remote_server_aws_fields(
            creds, mcp_url=resolve_aws_mcp_url("eu-central-1")
        )
        assert frankfurt_fields["aws_sigv4_region"] == "eu-central-1"

    def test_is_aws_mcp_url_requires_https(self):
        https_url = AWS_MCP_ENDPOINTS["us-east-1"]
        assert is_aws_mcp_url(https_url)
        assert not is_aws_mcp_url(https_url.replace("https://", "http://", 1))

    def test_endpoint_region_parsing(self):
        url = AWS_MCP_ENDPOINTS["us-east-1"]
        assert aws_mcp_endpoint_region(url) == "us-east-1"
        assert aws_mcp_endpoint_region("https://api.githubcopilot.com/mcp/") is None

    def test_sign_aws_mcp_http_request_adds_sigv4_headers(self, get_keys):
        headers = sign_aws_mcp_http_request(
            method="POST",
            url=AWS_MCP_ENDPOINTS["us-east-1"],
            body=b"{}",
            access_key_id=get_keys["AWS_ACCESS_KEY_ID"],
            secret_access_key=get_keys["AWS_SECRET_ACCESS_KEY"],
            session_token=get_keys.get("AWS_SESSION_TOKEN"),
            sigv4_region="us-east-1",
        )
        assert "Authorization" in headers
        assert "X-Amz-Date" in headers

    def test_resolve_aws_mcp_url_invalid(self):
        with pytest.raises(ValueError, match="Unsupported AWS MCP endpoint region"):
            resolve_aws_mcp_url("ap-south-1")
