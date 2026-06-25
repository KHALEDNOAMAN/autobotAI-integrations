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


class NessusService(BaseService):
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

    @staticmethod
    def get_all_python_sdk_clients():
        try:
            return NessusService.yaml_to_python_sdk_clients(
                importlib.resources.files("autobotAI_integrations.integrations.nessus")
                .joinpath("python_sdk_clients.yml")
                .read_text()
            )
        except Exception:
            return []

    @staticmethod
    def supported_connection_interfaces() -> List[ConnectionInterfaces]:
        return [ConnectionInterfaces.REST_API]

    @staticmethod
    def connection_interface_mapping() -> dict:
        return {ConnectionInterfaces.REST_API: NessusIntegration}

    @staticmethod
    def get_code_sample() -> str:
        try:
            return (
                importlib.resources.files("autobotAI_integrations.integrations.nessus")
                .joinpath("code_sample.py")
                .read_text()
            )
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

    @staticmethod
    def get_python_sdk_client(
        connection_details: Union[RestAPICreds, SDKCreds],
        task: PayloadTask,
    ) -> SDKClient:
        connection_details = connection_details.dict()

        client = NessusClient(
            url=connection_details.get("url"),
            access_key=connection_details.get("access_key"),
            secret_key=connection_details.get("secret_key"),
            verify_ssl=connection_details.get("verify_ssl", False),
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
