import importlib
import json
import re
from typing import List, Optional, Type, Union

import requests
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    RestAPICreds,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.models import IntegrationCategory

# ZWA uses a cloud-specific base URL, NOT the OneAPI endpoint (api.zsapi.net).
# The cloud attribute (e.g. "us1", "eu1") determines the subdomain.
# Default cloud is "us1".
ZWA_BASE_URL_TEMPLATE = "https://api.{cloud}.zsworkflow.net"
ZWA_DEFAULT_CLOUD = "us1"

# ZWA authenticates via its own key_id / key_secret pair (legacy auth, NOT OAuth2/ZIdentity).
# Token endpoint pattern — cloud-specific.
ZWA_TOKEN_URL_TEMPLATE = f"{ZWA_BASE_URL_TEMPLATE}/v1/auth/api-key/token"


def _parse_error_response(response: requests.Response) -> str:
    """
    Extract a human-readable error message from a Zscaler ZWA API response.
    Zscaler sometimes returns HTML error pages; this strips the HTML tags and
    returns only the meaningful text.
    """
    content_type = response.headers.get("Content-Type", "")
    body = response.text.strip()

    # Try JSON first
    if "application/json" in content_type:
        try:
            data = response.json()
            msg = (
                data.get("error_description")
                or data.get("error")
                or data.get("message")
            )
            if msg:
                return msg
        except Exception:
            pass

    # If HTML, strip tags/scripts and extract the meaningful message
    if "<html" in body.lower() or "<body" in body.lower():
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        text = re.sub(r"<[^>]+>", " ", cleaned)
        text = re.sub(r"\s+", " ", text).strip()

        # Look for Zscaler's "[error_code] message" pattern
        bracket_match = re.search(
            r"\[([^\]]+)\]\s*(.+?)(?:\s*Need help|\s*Visit\s+http|\s*$)", text
        )
        if bracket_match:
            error_code = bracket_match.group(1).strip()
            error_msg = bracket_match.group(2).strip()
            return f"{error_code}: {error_msg}"

        # "Error Status Message" table-like pattern
        status_match = re.search(
            r"(?:Error Status Message|Error)\s*(.+?)(?:\s*Need help|\s*Visit\s+http|\s*$)",
            text,
        )
        if status_match:
            return status_match.group(1).strip()

        # Strip Zscaler boilerplate and return remaining text
        text = re.sub(r"Need help\?.*$", "", text).strip()
        text = re.sub(r"Visit\s+https?://\S+", "", text).strip()
        text = re.sub(r"Zscaler Inc\.?", "", text).strip()
        if text:
            return text[:300]

    if len(body) > 300:
        return body[:300] + "..."
    return body or "Unknown error"


def _get_zwa_token(key_id: str, key_secret: str, cloud: str) -> str:
    """
    Authenticate to Zscaler Workflow Automation (ZWA) using its legacy
    key_id / key_secret credential pair.

    ZWA does NOT use the OneAPI OAuth2 / ZIdentity flow.
    It uses its own token endpoint scoped to the ZWA cloud region.

    Returns a Bearer access token on success, or raises on failure.
    """
    resolved_cloud = (cloud or ZWA_DEFAULT_CLOUD).strip().lower()
    token_url = ZWA_TOKEN_URL_TEMPLATE.format(cloud=resolved_cloud)

    payload = {
            "key_id": key_id,
            "key_secret": key_secret,
        }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(
        token_url,
        data=json.dumps(payload),
        headers=headers,
        timeout=15,
    )

    if not response.ok:
        msg = _parse_error_response(response)
        raise requests.exceptions.HTTPError(
            f"{response.status_code} - {msg}", response=response
        )

    data = response.json()
    # ZWA typically returns {"token": "..."} or {"access_token": "..."}
    access_token = data.get("token") or data.get("access_token")
    if not access_token:
        raise ValueError(
            f"ZWA token response did not contain a token. Response keys: {list(data.keys())}"
        )
    return access_token


class ZscalarWorkflowAutomationIntegration(BaseSchema):
    # Credentials — excluded from serialization
    key_id: Optional[str] = Field(default=None, exclude=True)
    key_secret: Optional[str] = Field(default=None, exclude=True)

    # Cloud region, e.g. "us1", "eu1". Determines which ZWA endpoint is called.
    cloud: Optional[str] = Field(default=ZWA_DEFAULT_CLOUD, exclude=False)

    # Test configuration — lets the user pick any ZWA endpoint for the health check
    test_method: Optional[str] = Field(default="post", exclude=False)
    test_api: Optional[str] = Field(default="/dlp/v1/incidents/search", exclude=False)
    test_body: Optional[str] = Field(default=json.dumps({"fields": [{"name": "priority","value": ["HIGH"]}]}), exclude=False)
    skip_test: Optional[bool] = Field(default=False, exclude=False)

    name: Optional[str] = "zscalar_workflow_automation"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Zscaler Workflow Automation (ZWA) enables automated security workflows, "
        "incident response, and policy orchestration across the Zscaler platform. "
        "Authentication uses the ZWA-native key_id / key_secret credential pair "
        "(not the OneAPI ZIdentity OAuth2 flow)."
    )


class ZscalarWorkflowAutomationService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ZscalarWorkflowAutomationIntegration, dict]):
        """
        Integration should have all the data regarding the ZWA integration.
        """
        if not isinstance(integration, ZscalarWorkflowAutomationIntegration):
            integration = ZscalarWorkflowAutomationIntegration(**integration)
        super().__init__(ctx, integration)

    def _resolved_base_url(self) -> str:
        cloud = (self.integration.cloud or ZWA_DEFAULT_CLOUD).strip().lower()
        return ZWA_BASE_URL_TEMPLATE.format(cloud=cloud)

    def _test_integration(self) -> dict:
        try:
            if self.integration.skip_test:
                return {"success": True}

            token = _get_zwa_token(
                key_id=self.integration.key_id,
                key_secret=self.integration.key_secret,
                cloud=self.integration.cloud,
            )

            base_url = self._resolved_base_url()
            test_url = f"{base_url}{self.integration.test_api}"
            http_method = getattr(requests, self.integration.test_method, requests.get)
            data = None
            if http_method == "post":
                data = self.integration.test_body if isinstance(self.integration.test_body, str) else json.dumps(self.integration.test_body)
            verify_resp = http_method(
                test_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                data=data,
                timeout=15,
            )

            if 200 <= verify_resp.status_code < 300:
                return {"success": True}
            else:
                msg = _parse_error_response(verify_resp)
                return {
                    "success": False,
                    "error": (
                        f"Token obtained but ZWA API check failed "
                        f"({verify_resp.status_code}): {msg}"
                    ),
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": (
                    "Connection is unreachable. Verify the ZWA cloud region is correct "
                    f"(current: '{self.integration.cloud or ZWA_DEFAULT_CLOUD}')."
                ),
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"Authentication failed: {e}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Zscaler Workflow Automation (ZWA)",
            "type": "form",
            "children": [
                {
                    "name": "key_id",
                    "type": "text/password",
                    "label": "ZWA Key ID",
                    "placeholder": "Enter your ZWA API Key ID",
                    "description": (
                        "ZWA API Key ID (key_id). "
                        "Generated under Administration > API Keys in the ZWA portal. "
                        "Also available as the ZWA_CLIENT_ID environment variable."
                    ),
                    "required": True,
                },
                {
                    "name": "key_secret",
                    "type": "text/password",
                    "label": "ZWA Key Secret",
                    "placeholder": "Enter your ZWA API Key Secret",
                    "description": (
                        "ZWA API Key Secret (key_secret). "
                        "Also available as the ZWA_CLIENT_SECRET environment variable."
                    ),
                    "required": True,
                },
                {
                    "name": "cloud",
                    "type": "text",
                    "label": "ZWA Cloud Region",
                    "placeholder": "e.g. us1",
                    "description": (
                        "ZWA cloud region prefix that determines the API endpoint. "
                        "Defaults to 'us1'. Common values: us1, eu1, ap1. "
                        "Check your ZWA portal URL for the correct region."
                    ),
                    "required": True,
                    "default": ZWA_DEFAULT_CLOUD,
                },
                {
                    "name": "test_api",
                    "type": "text",
                    "label": "Test HTTP API Path",
                    "placeholder": "Path suffix after the ZWA base URL",
                    "description": (
                        "API path to call when testing the integration. "
                        "Appended to https://api.{cloud}.zscaler.com"
                    ),
                    "required": True,
                    "default": "/dlp/v1/incidents/search",
                },
                {
                    "name": "test_method",
                    "type": "select",
                    "label": "Test HTTP Method",
                    "placeholder": "HTTP method for the test call",
                    "description": "HTTP method used when testing the integration.",
                    "required": True,
                    "options": [
                        {"label": "get", "value": "get"},
                        {"label": "head", "value": "head"},
                        {"label": "post", "value": "post"},
                    ],
                    "default": "post",
                },
                {
                    "name": "test_body",
                    "type": "text",
                    "label": "Test HTTP Body",
                    "placeholder": "Body to be sent in the api call",
                    "description": (
                        "Body to be sent in the api call. "
                        "Must be valid."
                    ),
                    "required": True,
                    "default": json.dumps({"fields": [{"name": "priority","value": ["HIGH"]}]}),
                },
                {
                    "name": "skip_test",
                    "type": "select",
                    "label": "Skip Integration Test",
                    "placeholder": "Skip the integration test",
                    "description": (
                        "If enabled, skips the credential test. "
                        "Useful when the ZWA API is not reachable from this environment."
                    ),
                    "required": True,
                    "options": [
                        {"label": "No", "value": False},
                        {"label": "Yes", "value": True},
                    ],
                    "default": False,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ZscalarWorkflowAutomationIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        """
        Authenticates via ZWA key_id/key_secret and returns REST API credentials
        with the Bearer token pre-injected into the Authorization header.
        """
        token = _get_zwa_token(
            key_id=self.integration.key_id,
            key_secret=self.integration.key_secret,
            cloud=self.integration.cloud,
        )
        return RestAPICreds(
            base_url=self._resolved_base_url(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        """
        Returns environment variables compatible with the Zscaler Python SDK's
        LegacyZWAClient, which reads ZWA_CLIENT_ID, ZWA_CLIENT_SECRET, and ZWA_CLOUD.
        """
        print(self._test_integration())
        envs = {
            "ZWA_CLIENT_ID": self.integration.key_id,
            "ZWA_CLIENT_SECRET": self.integration.key_secret,
            "ZWA_CLOUD": self.integration.cloud or ZWA_DEFAULT_CLOUD,
        }
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        """
        Builds execution combinations using the Zscaler Python SDK's LegacyZWAClient.
        The LegacyZWAClient is the correct client for ZWA — it does NOT use the
        OneAPI ZIdentity OAuth2 flow.
        """
        oneapi_module = importlib.import_module("zscaler.oneapi_client", package=None)
        LegacyZWAClient = getattr(oneapi_module, "LegacyZWAClient")

        config = {
            "key_id": payload_task.creds.envs.get("ZWA_CLIENT_ID"),
            "key_secret": payload_task.creds.envs.get("ZWA_CLIENT_SECRET"),
            "cloud": payload_task.creds.envs.get("ZWA_CLOUD", ZWA_DEFAULT_CLOUD),
            "logging": {"enabled": False, "verbose": False},
        }

        client = LegacyZWAClient(config)
        client.__enter__()

        return [
            {
                "clients": {
                    "zscalar": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]