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


class AcunetixIntegration(BaseSchema):
    url: str = Field(
        default="https://online.acunetix.com/api/v1",
        description="The base URL of the Acunetix Scanner instance (e.g. https://online.acunetix.com/api/v1 or on-premises URL)"
    )
    api_key: str = Field(..., exclude=True, description="The API Key for the Acunetix API")
    verify_ssl: bool = Field(default=False, description="Verify SSL certificates when communicating with Acunetix")

    name: Optional[str] = "Acunetix Web Application Security"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Acunetix is an automated web application security testing tool that audits your web applications "
        "by checking for vulnerabilities like SQL Injection, Cross-site Scripting, and other exploitable vulnerabilities."
    )


class AcunetixClient:
    """Custom self-contained Python client for the Acunetix API."""

    def __init__(self, url: str, api_key: str, verify_ssl: bool = False):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl

    def _headers(self) -> dict:
        return {
            "X-Auth": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def list_targets(self, limit: int = 1) -> requests.Response:
        """List scan targets. Used for connection validation."""
        endpoint = f"{self.url}/targets"
        return requests.get(
            endpoint,
            params={"limit": limit},
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=15
        )

    def list_scans(self) -> requests.Response:
        """List scan history and status in Acunetix."""
        endpoint = f"{self.url}/scans"
        return requests.get(
            endpoint,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=15
        )

    def list_all_vulnerabilities(self) -> requests.Response:
        """List all vulnerabilities found across scan targets."""
        endpoint = f"{self.url}/vulnerabilities"
        return requests.get(
            endpoint,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=15
        )

    def list_reports(self) -> requests.Response:
        """List generated vulnerability reports."""
        endpoint = f"{self.url}/reports"
        return requests.get(
            endpoint,
            headers=self._headers(),
            verify=self.verify_ssl,
            timeout=15
        )


class AcunetixService(BaseService):
    def __init__(self, ctx: dict, integration: Union[dict, BaseSchema]):
        if isinstance(integration, dict):
            integration = AcunetixIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Acunetix",
            "type": "form",
            "children": [
                {
                    "name": "url",
                    "type": "text",
                    "label": "Acunetix URL",
                    "placeholder": "https://online.acunetix.com/api/v1",
                    "required": True,
                    "default": "https://online.acunetix.com/api/v1",
                    "description": "The base URL of your Acunetix server (e.g. https://online.acunetix.com/api/v1 or https://localhost:3443/api/v1).",
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your Acunetix API Key",
                    "required": True,
                    "help_url": "https://www.acunetix.com/support/docs/generating-a-new-api-key/",
                    "help_url_text": "How to generate API Key ↗",
                },
                {
                    "name": "verify_ssl",
                    "type": "checkbox",
                    "label": "Verify SSL",
                    "default": False,
                    "description": "Verify SSL certificates when communicating with Acunetix.",
                },
            ],
        }

    @staticmethod
    def get_all_python_sdk_clients():
        try:
            return AcunetixService.yaml_to_python_sdk_clients(
                importlib.resources.files("autobotAI_integrations.integrations.acunetix")
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
        return {ConnectionInterfaces.REST_API: AcunetixIntegration}

    @staticmethod
    def get_code_sample() -> str:
        try:
            return (
                importlib.resources.files("autobotAI_integrations.integrations.acunetix")
                .joinpath("code_sample.py")
                .read_text()
            )
        except Exception:
            return ""

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return AcunetixIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            creds={
                "url": getattr(self.integration, "url", "https://online.acunetix.com/api/v1"),
                "api_key": getattr(self.integration, "api_key", ""),
                "verify_ssl": getattr(self.integration, "verify_ssl", False),
            }
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        url = getattr(self.integration, "url", "https://online.acunetix.com/api/v1").rstrip("/")
        api_key = getattr(self.integration, "api_key", "")
        verify_ssl = getattr(self.integration, "verify_ssl", False)
        return RestAPICreds(
            base_url=url,
            headers={
                "X-Auth": api_key,
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

        client = AcunetixClient(
            url=creds.get("url", "https://online.acunetix.com/api/v1"),
            api_key=creds.get("api_key", ""),
            verify_ssl=creds.get("verify_ssl", False),
        )

        return SDKClient(client=client)

    @classmethod
    def test_connection(cls, connection_details: Union[RestAPICreds, SDKCreds]) -> bool:
        try:
            client = cls.get_python_sdk_client(connection_details, None).client
            response = client.list_targets(limit=1)
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to connect to Acunetix: {str(e)}")

    def _test_integration(self) -> dict:
        try:
            client = AcunetixClient(
                url=getattr(self.integration, "url", "https://online.acunetix.com/api/v1"),
                api_key=getattr(self.integration, "api_key", ""),
                verify_ssl=getattr(self.integration, "verify_ssl", False),
            )
            response = client.list_targets(limit=1)
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}, details: {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to connect to Acunetix: {str(e)}"}
