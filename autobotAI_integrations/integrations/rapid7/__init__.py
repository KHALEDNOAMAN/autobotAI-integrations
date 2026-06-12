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

    name: Optional[str] = "Rapid7"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Rapid7 InsightVM is a vulnerability management platform that provides "
        "real-time visibility into vulnerabilities, assets, and risk across your "
        "entire environment via the Insight Platform Cloud API."
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


class Rapid7Service(BaseService):

    def __init__(self, ctx: dict, integration: Union[Rapid7Integration, dict]):
        if not isinstance(integration, Rapid7Integration):
            integration = Rapid7Integration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
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
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": (
                        f"Request failed with status code: {response.status_code}, "
                        f"details: {response.text}"
                    ),
                }
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
                    "required": True,
                    "description": (
                        "Generate an API key from the Rapid7 Insight Platform under "
                        "Administration > API Key Management."
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

        return [
            {
                "clients": {
                    "rapid7": rapid7_module.Rapid7Client(
                        api_key=payload_task.creds.envs.get("RAPID7_API_KEY"),
                        region=payload_task.creds.envs.get("RAPID7_REGION", "us"),
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        return SDKCreds(
            envs={
                "RAPID7_API_KEY": str(self.integration.api_key),
                "RAPID7_REGION": str(self.integration.region or "us"),
            }
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        region = self.integration.region or "us"
        return RestAPICreds(
            base_url=f"https://{region}.api.insight.rapid7.com",
            headers={"X-Api-Key": self.integration.api_key},
        )
