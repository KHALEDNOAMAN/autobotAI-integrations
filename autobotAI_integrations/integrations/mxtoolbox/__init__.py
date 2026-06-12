import importlib
import json
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


class MXToolboxIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "MXToolbox"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "MXToolbox is a suite of diagnostic, lookup, monitoring, and network verification tools."
    )


class MXToolboxClient:
    """Custom self-contained Python client for MXToolbox lookup queries."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mxtoolbox.com/api/v1"

    def lookup(self, command: str, argument: str) -> requests.Response:
        url = f"{self.base_url}/lookup/{command.strip('/')}/{argument.strip('/')}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = self.api_key
        return requests.get(url, headers=headers)


class MXToolboxService(BaseService):

    def __init__(self, ctx: dict, integration: Union[MXToolboxIntegration, dict]):
        if not isinstance(integration, MXToolboxIntegration):
            integration = MXToolboxIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # Check connectivity & credentials by looking up dns for example.com
            headers = {}
            if self.integration.api_key:
                headers["Authorization"] = str(self.integration.api_key)
            
            response = requests.get(
                "https://api.mxtoolbox.com/api/v1/lookup/dns/example.com",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}, details: {response.text}",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "MXToolbox",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the MXToolbox API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return MXToolboxIntegration

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
        mxtoolbox_module = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "mxtoolbox": mxtoolbox_module.MXToolboxClient(
                        payload_task.creds.envs.get("MXTOOLBOX_API_KEY")
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        return SDKCreds(envs={"MXTOOLBOX_API_KEY": str(self.integration.api_key)})

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://api.mxtoolbox.com/api/v1",
            headers={"Authorization": self.integration.api_key},
        )
