import importlib
from typing import Type, Union, List, Optional
from pydantic import Field
import requests

from autobotAI_integrations import BaseSchema, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import (
    IntegrationCategory,
    SDKClient,
    SDKCreds,
    RestAPICreds,
)
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements

RAPID7_REGIONS = ["us", "eu", "ap", "ca", "au", "jp"]


class Rapid7Integration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)
    region: Optional[str] = Field(default="us")
    console_url: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Rapid7"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Rapid7 InsightVM is a vulnerability management platform that provides "
        "real-time visibility into vulnerabilities, assets, and risk across your "
        "entire environment via the Insight Platform Cloud API (v4) and local Security Console API (v3)."
    )


class Rapid7Client:
    """Custom self-contained Python client for the Rapid7 Insight Platform Cloud API (v4)."""

    def __init__(self, api_key: str, region: str = "us"):
        self.api_key = api_key
        self.region = region if region in RAPID7_REGIONS else "us"
        self.base_url = f"https://{self.region}.api.insight.rapid7.com"

    def _headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def validate(self) -> requests.Response:
        """Test API key validity via the platform validate endpoint."""
        url = f"{self.base_url}/validate"
        return requests.get(url, headers=self._headers(), timeout=10)

    def get_assets(self, page: int = 0, size: int = 25) -> requests.Response:
        """List all assets in the InsightVM inventory (paginated)."""
        url = f"{self.base_url}/ivm/v4/assets"
        params = {"page": page, "size": size}
        return requests.get(url, headers=self._headers(), params=params, timeout=30)

    def get_asset(self, asset_id: str) -> requests.Response:
        """Get details for a single asset by its ID."""
        url = f"{self.base_url}/ivm/v4/assets/{asset_id}"
        return requests.get(url, headers=self._headers(), timeout=15)

    def get_asset_vulnerabilities(
        self, asset_id: str, page: int = 0, size: int = 25
    ) -> requests.Response:
        """List all vulnerabilities found on a specific asset."""
        url = f"{self.base_url}/ivm/v4/assets/{asset_id}/vulnerabilities"
        params = {"page": page, "size": size}
        return requests.get(url, headers=self._headers(), params=params, timeout=30)

    def get_vulnerabilities(self, page: int = 0, size: int = 25) -> requests.Response:
        """List all known vulnerabilities across the platform (paginated)."""
        url = f"{self.base_url}/ivm/v4/vulnerabilities"
        params = {"page": page, "size": size}
        return requests.get(url, headers=self._headers(), params=params, timeout=30)

    def get_vulnerability(self, vuln_id: str) -> requests.Response:
        """Get details for a specific vulnerability by its ID."""
        url = f"{self.base_url}/ivm/v4/vulnerabilities/{vuln_id}"
        return requests.get(url, headers=self._headers(), timeout=15)

    def get_scan_engines(self) -> requests.Response:
        """List all scan engines configured in the platform."""
        url = f"{self.base_url}/ivm/v4/scan-engines"
        return requests.get(url, headers=self._headers(), timeout=15)

    def get_sites(self, page: int = 0, size: int = 25) -> requests.Response:
        """List all sites (scan targets/groups) in the platform."""
        url = f"{self.base_url}/ivm/v4/sites"
        params = {"page": page, "size": size}
        return requests.get(url, headers=self._headers(), params=params, timeout=30)

    def get_health(self) -> requests.Response:
        """Check the health and operational status of the Insight Platform cloud services."""
        url = f"{self.base_url}/vm/admin/health"
        return requests.get(url, headers=self._headers(), timeout=10)

    def get_integration_assets(self, page: int = 0, size: int = 25) -> requests.Response:
        """Retrieve assets optimized for third-party integrations and data extraction pipelines."""
        url = f"{self.base_url}/vm/v4/integration/assets"
        params = {"page": page, "size": size}
        return requests.get(url, headers=self._headers(), params=params, timeout=30)


class Rapid7ConsoleV3Client:
    """Custom self-contained Python client for the Rapid7 InsightVM Security Console REST API (v3)."""

    def __init__(
        self,
        console_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.console_url = console_url.rstrip("/") if console_url else ""
        self.username = username or ""
        self.password = password or ""

    def _auth(self):
        if self.username and self.password:
            return (self.username, self.password)
        return None

    def _headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def trigger_site_scan(self, site_id: int) -> requests.Response:
        """Trigger an active vulnerability scan on a specific site."""
        url = f"{self.console_url}/api/3/sites/{site_id}/scans"
        return requests.post(
            url, headers=self._headers(), auth=self._auth(), timeout=30
        )

    def get_scan_status(self, scan_id: int) -> requests.Response:
        """Get the status of an active or past scan."""
        url = f"{self.console_url}/api/3/scans/{scan_id}"
        return requests.get(
            url, headers=self._headers(), auth=self._auth(), timeout=15
        )

    def stop_scan(self, scan_id: int) -> requests.Response:
        """Stop/abort a currently running scan."""
        url = f"{self.console_url}/api/3/scans/{scan_id}/stop"
        return requests.post(
            url, headers=self._headers(), auth=self._auth(), timeout=30
        )

    def generate_report(self, report_id: int) -> requests.Response:
        """Generate a vulnerability report instance."""
        url = f"{self.console_url}/api/3/reports/{report_id}/generate"
        return requests.post(
            url, headers=self._headers(), auth=self._auth(), timeout=30
        )


class Rapid7Service(BaseService):

    def __init__(self, ctx: dict, integration: Union[Rapid7Integration, dict]):
        if not isinstance(integration, Rapid7Integration):
            integration = Rapid7Integration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            has_cloud = bool(self.integration.api_key)
            has_console = bool(
                self.integration.console_url
                and self.integration.username
                and self.integration.password
            )
            if not has_cloud and not has_console:
                return {
                    "success": False,
                    "error": "No credentials configured. Provide an Insight Platform API key (v4) or Security Console URL + username + password (v3).",
                }

            if self.integration.api_key:
                region = self.integration.region or "us"
                validate_url = f"https://{region}.api.insight.rapid7.com/validate"
                response = requests.get(
                    validate_url,
                    headers={
                        "X-Api-Key": str(self.integration.api_key),
                        "Accept": "application/json",
                    },
                    timeout=10,
                )
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": (
                            f"Cloud API v4 validate failed with status code: {response.status_code}, "
                            f"details: {response.text}"
                        ),
                    }

            if self.integration.console_url and self.integration.username and self.integration.password:
                console_url = self.integration.console_url.rstrip("/")
                test_url = f"{console_url}/api/3/administration/info"
                response = requests.get(
                    test_url,
                    auth=(str(self.integration.username), str(self.integration.password)),
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Console API v3 check failed with status code: {response.status_code}",
                    }

            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Rapid7",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your Rapid7 Insight Platform API Key",
                    "required": False,
                    "description": (
                        "Generate an API key from the Rapid7 Insight Platform under "
                        "Administration > API Key Management (required for Cloud API v4)."
                    ),
                },
                {
                    "name": "region",
                    "type": "select",
                    "label": "Region",
                    "placeholder": "Select your Insight Platform region",
                    "required": True,
                    "default": "us",
                    "options": [
                        {"label": "United States (us)", "value": "us"},
                        {"label": "Europe (eu)", "value": "eu"},
                        {"label": "Asia Pacific (ap)", "value": "ap"},
                        {"label": "Canada (ca)", "value": "ca"},
                        {"label": "Australia (au)", "value": "au"},
                        {"label": "Japan (jp)", "value": "jp"},
                    ],
                },
                {
                    "name": "console_url",
                    "type": "text",
                    "label": "Security Console URL (Optional - for v3 API)",
                    "placeholder": "https://your-console.example.com:3780",
                    "required": False,
                    "description": (
                        "Required only if using local Security Console REST API v3 via Python SDK (rapid7_console client)."
                    ),
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Security Console Username (Optional - for v3 API)",
                    "placeholder": "Enter your Security Console username",
                    "required": False,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "Security Console Password (Optional - for v3 API)",
                    "placeholder": "Enter your Security Console password",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return Rapid7Integration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
            "preview": True,
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        rapid7_module = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        clients = {}
        api_key = payload_task.creds.envs.get("RAPID7_API_KEY")
        if api_key:
            clients["rapid7"] = rapid7_module.Rapid7Client(
                api_key=api_key,
                region=payload_task.creds.envs.get("RAPID7_REGION", "us"),
            )

        console_url = payload_task.creds.envs.get("RAPID7_CONSOLE_URL")
        if console_url:
            clients["rapid7_console"] = rapid7_module.Rapid7ConsoleV3Client(
                console_url=console_url,
                username=payload_task.creds.envs.get("RAPID7_CONSOLE_USERNAME"),
                password=payload_task.creds.envs.get("RAPID7_CONSOLE_PASSWORD"),
            )

        return [
            {
                "clients": clients,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        return SDKCreds(
            envs={
                "RAPID7_API_KEY": str(self.integration.api_key or ""),
                "RAPID7_REGION": str(self.integration.region or "us"),
                "RAPID7_CONSOLE_URL": str((self.integration.console_url or "").rstrip("/")),
                "RAPID7_CONSOLE_USERNAME": str(self.integration.username or ""),
                "RAPID7_CONSOLE_PASSWORD": str(self.integration.password or ""),
            }
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        region = self.integration.region or "us"
        return RestAPICreds(
            base_url=f"https://{region}.api.insight.rapid7.com",
            headers={"X-Api-Key": self.integration.api_key},
        )
