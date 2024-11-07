import importlib
from typing import List, Optional, Union

from pydantic import Field, field_validator

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


class OktaIntegration(BaseSchema):
    host_url: str
    token: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Okta is the leading independent identity provider. The Okta Identity enables organizations to securely connect the right people to the right technologies at the right time."
    )
    
    @field_validator("host_url", mode='before')
    def validate_host_url(cls, value):
        if not value.startswith("https://"):
            raise ValueError("Host URL must start with 'https://'")
        return value.strip('/')


class OktaService(BaseService):

    def __init__(self, ctx: dict, integration: Union[OktaIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, OktaIntegration):
            integration = OktaIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False):
        try:
            response = requests.get(
                url=self.integration.host_url + '/api/v1/users',
                headers={"Authorization": f"SSWS {self.integration.token}"}
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is Unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Okta",
            "type": "form",
            "children": [
                {
                    "name": "host_url",
                    "type": "text/url",
                    "label": "Okta Host URL",
                    "placeholder": "Enter HOST URL",
                    "required": True,
                },
                {
                    "name": "token",
                    "type": "text/password",
                    "label": "Okta API Token",
                    "placeholder": "Enter API Token",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema():
        return OktaIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        okta = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        config = {
            "orgUrl": payload_task.creds.envs.get("OKTA_CLIENT_ORGURL"),
            "token": payload_task.creds.envs.get("OKTA_CLIENT_TOKEN"),
        }

        return [
            {
                "clients": {
                    "okta": okta.Client(config),
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "OKTA_CLIENT_ORGURL": self.integration.host_url,
            "OKTA_CLIENT_TOKEN": self.integration.token,
        }
        conf_path = "~/.steampipe/config/okta.spc"
        config = """connection "okta" {
  plugin = "okta"

}"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="okta",
            connection_name="okta",
            conf_path=conf_path,
            config=config,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "OKTA_CLIENT_ORGURL": self.integration.host_url,
            "OKTA_CLIENT_TOKEN": self.integration.token,
        }
        return SDKCreds(envs=envs)
