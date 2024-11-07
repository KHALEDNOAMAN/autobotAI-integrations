import importlib
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    CLICreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)

from autobotAI_integrations.models import IntegrationCategory
import requests


class DATADOGIntegration(BaseSchema):
    api_url: str = Field(default="https://api.datadoghq.com/")
    api_key: Optional[str] = Field(default=None, exclude=True)
    app_key: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Datadog is the essential monitoring and security platform for cloud applications."
    )


class DATADOGService(BaseService):

    def __init__(self, ctx: dict, integration: Union[DATADOGIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, DATADOGIntegration):
            integration = DATADOGIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False):
        try:
            headers = {
                "Accept": "application/json",
                "DD-API-KEY": str(self.integration.api_key),
            }

            # Make the API request
            url = self.integration.api_url + "" if str(self.integration.api_url).endswith("/") else "/"
            response = requests.get(f"{url}api/v1/validate", headers=headers)
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Datadog",
            "type": "form",
            "children": [
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "Datadog API Key",
                    "placeholder": "Enter API Key",
                    "required": True,
                },
                {
                    "name": "app_key",
                    "type": "text/password",
                    "label":"Datadog Application Key",
                    "placeholder": "Enter Application Key",
                    "description": "Application key is required for some endpoints. You can get it from your Datadog account settings.",
                    "required": True,
                },
                {
                    "name": "api_url",
                    "type": "text/url",
                    "label":"API URL",
                    "placeholder": "Enter HOST URL",
                    "description": "All Datadog API clients are configured by default to consume Datadog US site APIs. If you are on the Datadog EU site use 'https://api.datadoghq.eu' and free trial accounts works only on 'https://us5.datadoghq.com/'",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema():
        return DATADOGIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        datadog = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )

        datadog.initialize(
            api_key=payload_task.creds.envs.get("DATADOG_API_KEY"),
            app_key=payload_task.creds.envs.get("DATADOG_APP_KEY"),
            api_host=payload_task.creds.envs.get("DATADOG_HOST")
        )

        return [
            {
                "clients": {
                    "datadog_api_client": datadog.api,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "DD_CLIENT_API_KEY": self.integration.api_key,
            "DD_CLIENT_APP_KEY": self.integration.app_key,
        }
        conf_path = "~/.steampipe/config/datadog.spc"
        config = f"""connection "datadog" {{
  plugin = "datadog"

  api_url = "{self.integration.api_url}"
}}"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="datadog",
            connection_name="datadog",
            conf_path=conf_path,
            config=config,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "DATADOG_API_KEY": self.integration.api_key,
            "DATADOG_APP_KEY": self.integration.app_key,
            "DATADOG_HOST": self.integration.api_url
        }
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        pass
