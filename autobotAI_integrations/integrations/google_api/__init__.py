from typing import List, Type, Union
import importlib
import json

from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    SteampipeCreds,
    PayloadTask,
    SDKClient,
)

from google.oauth2.service_account import Credentials
from autobotAI_integrations.integrations.gcp import GCPCredentials, GCPService, GCPIntegration


class GoogleAPIsIntegration(GCPIntegration):
    name: Optional[str] = "Google APIs"
    description: Optional[str] = (
        "Google APIs are a set of tools that allow developers to programmatically access and interact with Google's services and data."
    )


class GoogleAPIsService(GCPService, BaseService):

    def __init__(self, ctx: dict, integration: Union[GoogleAPIsIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GoogleAPIsIntegration):
            integration = GoogleAPIsIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Google APIs",
            "type": "form",
            "children": [
                {
                    "name": "credentials",
                    "type": "json",
                    "label": "Credentials JSON",
                    "placeholder": "Enter the Credentials In JSON Format",
                    "required": True,
                }
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GoogleAPIsIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["compliance_supported"] = False
        return details

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "(~/.steampipe/config/googleworkspace.spc"
        config = """connection "googleworkspace" {
  plugin    = "googleworkspace"

}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="googleworkspace",
            connection_name="googleworkspace",
            conf_path=conf_path,
            config=config,
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:

        clients_classes = dict()
        credentials_dict = GCPCredentials.model_validate_json(
            json.loads(payload_task.creds.envs["GOOGLE_APPLICATION_CREDENTIALS"])
        ).model_dump()

        credentials = Credentials.from_service_account_info(
            credentials_dict
        )
        for client in client_definitions:
            try:
                print(client.model_dump_json(indent=2))
                discovery = importlib.import_module(client.module, package=None)
                name, version = client.name.split("_")
                clients_classes[client.name] = discovery.build(
                    serviceName=name, version=version,
                    credentials=credentials,
                )
            except BaseException as e:
                print(e)
                continue
        return [
            {
                "clients": clients_classes,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
