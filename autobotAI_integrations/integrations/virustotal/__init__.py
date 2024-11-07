import base64
import importlib
from typing import List, Optional, Type, Union
import uuid

from pydantic import Field
import requests
from autobotAI_integrations import BaseService
from autobotAI_integrations.models import BaseSchema, CLICreds, ConnectionInterfaces, IntegrationCategory, SDKClient, SDKCreds, SteampipeCreds
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements


class VirusTotalIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "VirusTotal"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "VirusTotal is a free online service that analyzes files and URLs for malicious content using multiple antivirus engines and threat intelligence sources"
    )


class VirusTotalService(BaseService):

    def __init__(self, ctx: dict, integration: Union[VirusTotalIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, VirusTotalIntegration):
            integration = VirusTotalIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False) -> dict:
        url = "https://example.com/"
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers = {
            "accept": "application/json",
            "x-apikey": str(self.integration.api_key),
        }

        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            return {"success": True}
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed. {e}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "VirusTotal",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the VirusTotal API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return VirusTotalIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "VTCLI_APIKEY": str(self.integration.api_key),
        }
        conf_path = "~/.steampipe/config/virustotal.spc"
        config = """connection "virustotal" {
  plugin  = "virustotal"
}
"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="virustotal",
            connection_name="virustotal",
            conf_path=conf_path,
            config=config,
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        vt = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "virustotal": vt.Client(payload_task.creds.envs.get("VTCLI_APIKEY"))
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {
            "VTCLI_APIKEY": str(self.integration.api_key),
        }
        return SDKCreds(envs=creds)
