import importlib
import os
import inspect
import yaml
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


class NessusIntegration(BaseSchema):
    url: str = Field(
        default="https://localhost:8834", description="The base URL of the Nessus Scanner instance"
    )
    access_key: str = Field(..., exclude=True, description="The Access Key for the Nessus API")
    secret_key: str = Field(..., exclude=True, description="The Secret Key for the Nessus API")
    verify_ssl: bool = Field(default=False, description="Whether to verify SSL certificates")

    name: Optional[str] = "Nessus Vulnerability Scanner"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Nessus is a proprietary vulnerability scanner developed by Tenable, Inc. "
        "This integration allows you to interact with the Nessus API to manage scans and retrieve results."
    )


class NessusClient:
    """Custom self-contained Python client for the Nessus API."""

    def __init__(self, url: str, access_key: str, secret_key: str, verify_ssl: bool = False):
        self.url = url.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.verify_ssl = verify_ssl

    def _headers(self) -> dict:
        return {
            "X-ApiKeys": f"accessKey={self.access_key}; secretKey={self.secret_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def server_properties(self) -> requests.Response:
        """Get the Nessus server properties. Used for connection validation."""
        endpoint = f"{self.url}/server/properties"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=10)

    def list_scans(self) -> requests.Response:
        """List all scans in Nessus."""
        endpoint = f"{self.url}/scans"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def get_scan_details(self, scan_id: int) -> requests.Response:
        """Get details of a specific scan."""
        endpoint = f"{self.url}/scans/{scan_id}"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def server_status(self) -> requests.Response:
        """Returns the Nessus server status and health details."""
        endpoint = f"{self.url}/server/status"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=10)

    def list_scan_templates(self) -> requests.Response:
        """List all available scan templates (e.g., Basic Network Scan, Host Discovery) and their UUIDs."""
        endpoint = f"{self.url}/editor/scan/templates"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def list_policies(self) -> requests.Response:
        """Returns the list of configured vulnerability scan policies."""
        endpoint = f"{self.url}/policies"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def create_scan(
        self,
        uuid: str,
        name: str,
        text_targets: str,
        description: str = "",
        folder_id: Optional[int] = None,
        policy_id: Optional[int] = None,
    ) -> requests.Response:
        """Create a new vulnerability scan for target IP addresses or subnets."""
        endpoint = f"{self.url}/scans"
        payload = {
            "uuid": uuid,
            "settings": {
                "name": name,
                "text_targets": text_targets,
                "description": description,
            },
        }
        if folder_id is not None:
            payload["settings"]["folder_id"] = folder_id
        if policy_id is not None:
            payload["settings"]["policy_id"] = policy_id
        return requests.post(
            endpoint, headers=self._headers(), json=payload, verify=self.verify_ssl, timeout=30
        )

    def delete_scans(self, ids: List[int]) -> requests.Response:
        """Delete scans in bulk by their IDs."""
        endpoint = f"{self.url}/scans"
        payload = {"ids": ids}
        return requests.delete(
            endpoint, headers=self._headers(), json=payload, verify=self.verify_ssl, timeout=30
        )

    def launch_scan(self, scan_id: int) -> requests.Response:
        """Trigger an existing vulnerability scan to run immediately."""
        endpoint = f"{self.url}/scans/{scan_id}/launch"
        return requests.post(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def pause_scan(self, scan_id: int) -> requests.Response:
        """Temporarily pause a running vulnerability scan."""
        endpoint = f"{self.url}/scans/{scan_id}/pause"
        return requests.post(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def resume_scan(self, scan_id: int) -> requests.Response:
        """Resume a previously paused vulnerability scan."""
        endpoint = f"{self.url}/scans/{scan_id}/resume"
        return requests.post(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def stop_scan(self, scan_id: int) -> requests.Response:
        """Stop a running vulnerability scan."""
        endpoint = f"{self.url}/scans/{scan_id}/stop"
        return requests.post(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def kill_scan(self, scan_id: int) -> requests.Response:
        """Forcefully terminate a running vulnerability scan faster than stop."""
        endpoint = f"{self.url}/scans/{scan_id}/kill"
        return requests.post(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def export_scan(
        self, scan_id: int, format: str = "nessus", chapters: Optional[str] = None
    ) -> requests.Response:
        """Request export of vulnerability scan results into a specified file format (e.g., nessus, csv, pdf, html)."""
        endpoint = f"{self.url}/scans/{scan_id}/export"
        payload = {"format": format}
        if chapters is not None:
            payload["chapters"] = chapters
        return requests.post(
            endpoint, headers=self._headers(), json=payload, verify=self.verify_ssl, timeout=30
        )

    def get_export_status(self, scan_id: int, file_id: int) -> requests.Response:
        """Check the generation status of a requested scan export file."""
        endpoint = f"{self.url}/scans/{scan_id}/export/{file_id}/status"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def download_export(self, scan_id: int, file_id: int) -> requests.Response:
        """Download a generated vulnerability scan export file once its status is ready."""
        endpoint = f"{self.url}/scans/{scan_id}/export/{file_id}/download"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=60)

    def list_scanners(self) -> requests.Response:
        """Returns the list of local and linked remote/cloud scanners."""
        endpoint = f"{self.url}/scanners"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)

    def list_folders(self) -> requests.Response:
        """Returns the list of scan folders (e.g., My Scans, Trash)."""
        endpoint = f"{self.url}/folders"
        return requests.get(endpoint, headers=self._headers(), verify=self.verify_ssl, timeout=30)


class NessusService(BaseService):
    def __init__(self, ctx: dict, integration: Union[dict, BaseSchema]):
        if isinstance(integration, dict):
            integration = NessusIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Nessus",
            "type": "form",
            "children": [
                {
                    "name": "url",
                    "type": "text",
                    "label": "Scanner URL",
                    "placeholder": "https://localhost:8834",
                    "required": True,
                    "default": "https://localhost:8834",
                    "description": "The base URL of your Nessus Vulnerability Scanner instance.",
                },
                {
                    "name": "access_key",
                    "type": "text/password",
                    "label": "Access Key",
                    "placeholder": "Enter your Nessus API Access Key",
                    "required": True,
                },
                {
                    "name": "secret_key",
                    "type": "text/password",
                    "label": "Secret Key",
                    "placeholder": "Enter your Nessus API Secret Key",
                    "required": True,
                },
                {
                    "name": "verify_ssl",
                    "type": "checkbox",
                    "label": "Verify SSL",
                    "default": False,
                    "description": "Verify SSL certificates when communicating with Nessus.",
                },
            ],
        }

    @classmethod
    def get_all_python_sdk_clients(cls, integration_type=None):
        try:
            base_path = os.path.dirname(inspect.getfile(cls))
            with open(os.path.join(base_path, "python_sdk_clients.yml"), "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return []

    @staticmethod
    def supported_connection_interfaces() -> List[ConnectionInterfaces]:
        return [ConnectionInterfaces.REST_API, ConnectionInterfaces.PYTHON_SDK]

    @staticmethod
    def connection_interface_mapping() -> dict:
        return {
            ConnectionInterfaces.REST_API: NessusIntegration,
            ConnectionInterfaces.PYTHON_SDK: NessusIntegration,
        }

    @classmethod
    def get_code_sample(cls) -> str:
        try:
            base_path = os.path.dirname(inspect.getfile(cls))
            with open(os.path.join(base_path, "code_sample.py"), "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return NessusIntegration

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

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            creds={
                "url": getattr(self.integration, "url", "https://localhost:8834"),
                "access_key": getattr(self.integration, "access_key", ""),
                "secret_key": getattr(self.integration, "secret_key", ""),
                "verify_ssl": getattr(self.integration, "verify_ssl", False),
            }
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        url = getattr(self.integration, "url", "https://localhost:8834").rstrip("/")
        access_key = getattr(self.integration, "access_key", "")
        secret_key = getattr(self.integration, "secret_key", "")
        verify_ssl = getattr(self.integration, "verify_ssl", False)
        return RestAPICreds(
            base_url=url,
            headers={
                "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            verify_ssl=verify_ssl,
        )

    @staticmethod
    def get_python_sdk_client(
        connection_details: Union[RestAPICreds, SDKCreds],
        task: PayloadTask,
    ) -> SDKClient:
        details_dict = connection_details.dict()
        creds = details_dict.get("creds") or details_dict

        client = NessusClient(
            url=creds.get("url", "https://localhost:8834"),
            access_key=creds.get("access_key", ""),
            secret_key=creds.get("secret_key", ""),
            verify_ssl=creds.get("verify_ssl", False),
        )

        return SDKClient(client=client)

    @classmethod
    def test_connection(cls, connection_details: Union[RestAPICreds, SDKCreds]) -> bool:
        try:
            client = cls.get_python_sdk_client(connection_details, None).client
            response = client.server_properties()
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to connect to Nessus: {str(e)}")

    def _test_integration(self) -> dict:
        try:
            client = NessusClient(
                url=getattr(self.integration, "url", "https://localhost:8834"),
                access_key=getattr(self.integration, "access_key", ""),
                secret_key=getattr(self.integration, "secret_key", ""),
                verify_ssl=getattr(self.integration, "verify_ssl", False),
            )
            response = client.server_properties()
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}, details: {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to connect to Nessus: {str(e)}"}

