import importlib
from typing import List, Optional, Type, Union

from pydantic import Field
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    SDKClient,
    SDKCreds,
    SteampipeCreds,
)
from autobotAI_integrations import BaseService
import requests

from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements


class ShodanIntegration(BaseSchema):
    api_key: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Shodan is a search engine for Internet-connected devices, allowing users to find specific types of devices and vulnerabilities by scanning and indexing IP addresses."
    )


class ShodanService(BaseService):

    def __init__(self, ctx: dict, integration: Union[ShodanIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, ShodanIntegration):
            integration = ShodanIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        url = "https://api.shodan.io/account/profile?key={}".format(
            self.integration.api_key
        )
        response = requests.get(url)
        if response.status_code == 200:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"Request failed with status code: {response.status_code}",
            }

    @staticmethod
    def get_forms():
        return {
            "label": "Shodan",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter the Shodan API Key",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ShodanIntegration

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
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {
            "SHODAN_API_KEY": str(self.integration.api_key)
        }
        conf_path = "~/.steampipe/config/shodan.spc"
        config = """connection "shodan" {
  plugin = "shodan"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="shodan",
            connection_name="shodan",
            conf_path=conf_path,
            config=config,
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        shodan = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        return [
            {
                "clients": {
                    "shodan": shodan.Shodan(
                        payload_task.creds.envs.get("SHODAN_API_KEY")
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {
            "SHODAN_API_KEY": str(self.integration.api_key),
        }
        return SDKCreds(envs=creds)
