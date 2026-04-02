import importlib
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

def _parse_error_response(response: requests.Response) -> str:
    """
    Extract a human-readable error message from a Zscaler API response.
    Zscaler often returns HTML error pages; this strips the HTML and
    returns just the meaningful text.
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

    # If HTML, strip tags and scripts, then extract the status message
    if "<html" in body.lower() or "<body" in body.lower():
        # Remove <script> and <style> blocks entirely
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        # Strip remaining HTML tags
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

        # Look for "Error Status Message" pattern in table-like output
        status_match = re.search(
            r"(?:Error Status Message|Error)\s*(.+?)(?:\s*Need help|\s*Visit\s+http|\s*$)",
            text,
        )
        if status_match:
            return status_match.group(1).strip()

        # Fallback: return cleaned text without boilerplate
        # Remove common Zscaler boilerplate
        text = re.sub(r"Need help\?.*$", "", text).strip()
        text = re.sub(r"Visit\s+https?://\S+", "", text).strip()
        text = re.sub(r"Zscaler Inc\.?", "", text).strip()
        if text:
            return text[:300]

    # Fallback: return raw body truncated
    if len(body) > 300:
        return body[:300] + "..."
    return body or "Unknown error"


def _get_token(client_id: str, client_secret: str, vanity_domain: str, cloud: Optional[str] = None) -> str:
    """
    Authenticate to Zscaler OneAPI using the OAuth2 client_credentials grant.
    Returns a Bearer access token on success or raises on failure.
    """

    # The SDK handles token acquisition and refresh automatically
    token_url = f"https://{vanity_domain.strip()}.zslogin.net/oauth2/v1/token"
    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not response.ok:
        msg = _parse_error_response(response)
        raise requests.exceptions.HTTPError(
            f"{response.status_code} - {msg}", response=response
        )
    access_token = None
    try:
        data = response.json()
        access_token = data.get("access_token")
    except:
        match = re.search(r'authnToken:\s*"([^"]+)"', response.text)
        if match:
            access_token = match.group(1)

    if not access_token:
        raise ValueError("Token response did not contain an access_token")
    return access_token


class ZscalerIntegration(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    vanity_domain: Optional[str] = Field(default=None, exclude=False)
    cloud: Optional[str] = Field(default=None, exclude=False)
    test_method: Optional[str] = Field(default=None, exclude=False)
    test_api: Optional[str] = Field(default=None, exclude=False)

    name: Optional[str] = "Zscaler"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Zscaler is a cloud-native zero trust platform providing secure internet and SaaS access, "
        "advanced threat protection, data loss prevention, and zero trust connectivity "
        "for users, workloads, and devices across ZIA, ZPA, ZDX, and more."
    )


class ZscalerService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ZscalerIntegration, dict]):
        """
        Integration should have all the data regarding the integration.
        """
        if not isinstance(integration, ZscalerIntegration):
            integration = ZscalerIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            ONEAPI_BASE_URL = "https://api.zsapi.net"
            self.integration.cloud = "" if not self.integration.cloud else self.integration.cloud
            if self.integration.cloud:
                ONEAPI_BASE_URL = f"https://api.{self.integration.cloud}.zscaler.com"



            token = _get_token(
                client_id=self.integration.client_id,
                client_secret=self.integration.client_secret,
                vanity_domain=self.integration.vanity_domain.strip(),
                cloud=self.integration.cloud
            )
            verify_resp = getattr(requests, self.integration.test_method, requests.get)(
                f"{ONEAPI_BASE_URL}{self.integration.test_api}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )
            if verify_resp.status_code < 200 or verify_resp.status_code >= 300:
                return {"success": False, "error": f"status code: {verify_resp.status_code}\nerror message: {verify_resp.text}"}
            return {"success": True}
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection is unreachable. Verify the vanity domain is correct.",
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
            "label": "Zscaler",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text/password",
                    "label": "Client ID",
                    "placeholder": "Enter your Zscaler API Client ID",
                    "description": "API Client ID from ZIdentity (Administration > API Clients)",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Zscaler API Client Secret",
                    "required": True,
                },
                {
                    "name": "vanity_domain",
                    "type": "text",
                    "label": "Vanity Domain",
                    "placeholder": "e.g. mycompany",
                    "description": "Your organization's vanity domain (the part before .zslogin.net)",
                    "required": True,
                },
                {
                    "name": "cloud",
                    "type": "text",
                    "label": "Cloud",
                    "placeholder": "Leave Empty if .zslogin.net",
                    "description": "Your organization's custom cloud parameter, i.e. mycompany.zslogin{cloud}.net",
                    "required": False,
                },
                {
                    "name": "cloud",
                    "type": "text",
                    "label": "Cloud",
                    "placeholder": "Leave Empty if .zslogin.net",
                    "description": "Your organization's custom cloud parameter, i.e. mycompany.zslogin{cloud}.net",
                    "required": False,
                },
                {
                    "name": "test_api",
                    "type": "text",
                    "label": "Test API",
                    "placeholder": "API to hit to test integration",
                    "description": "API to hit to test integration",
                    "required": True,
                },
                {
                    "name": "test_method",
                    "type": "text",
                    "label": "Test Method",
                    "placeholder": "Method to hit the api with",
                    "description": "Method to hit the api with",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ZscalerIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        """
        Authenticates via OneAPI client_credentials and returns REST API
        credentials with the Bearer token injected into the headers.
        """
        self.integration.cloud = "" if not self.integration.cloud else self.integration.cloud
        token = _get_token(
            client_id=self.integration.client_id,
            client_secret=self.integration.client_secret,
            vanity_domain=self.integration.vanity_domain,
            cloud=self.integration.cloud,
        )
        ONEAPI_BASE_URL = "https://api.zsapi.net"
        if self.integration.cloud:
            ONEAPI_BASE_URL = f"https://api.{self.integration.cloud}.zscaler.com"
        return RestAPICreds(
            base_url=f"{ONEAPI_BASE_URL}/zia",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "ZSCALER_CLIENT_ID": self.integration.client_id,
            "ZSCALER_CLIENT_SECRET": self.integration.client_secret,
            "ZSCALER_VANITY_DOMAIN": self.integration.vanity_domain,
            "ZSCALER_CLOUD": "" if not self.integration.cloud else self.integration.cloud,
        }
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        zscaler_module = importlib.import_module("zscaler", package=None)
        ZscalerClient = getattr(zscaler_module, "ZscalerClient")

        config = {
            "clientId": payload_task.creds.envs.get("ZSCALER_CLIENT_ID"),
            "clientSecret": payload_task.creds.envs.get("ZSCALER_CLIENT_SECRET"),
            "vanityDomain": payload_task.creds.envs.get("ZSCALER_VANITY_DOMAIN"),
            "cloud": payload_task.creds.envs.get("ZSCALER_CLOUD"),
        }

        client = ZscalerClient(config)
        client.__enter__()

        return [
            {
                "clients": {
                    "zscaler": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
