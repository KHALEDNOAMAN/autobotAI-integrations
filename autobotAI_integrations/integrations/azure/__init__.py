from typing import Type, Union
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements,PayloadTask
from autobotAI_integrations.models import *

import uuid
import importlib

from azure.identity import ClientSecretCredential

class AzureIntegration(BaseSchema):
    account_id: Optional[str] = uuid.uuid4().hex
    tenant_id: Optional[str] = Field(default=None, exclude=True)
    client_id: Optional[str] = Field(default=None, exclude=True)
    subscription_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = None
    
    def __init__(self, **kwargs):
        kwargs["accountId"] = self.account_id
        super().__init__(**kwargs)


class AzureService(BaseService):

    def __init__(self, ctx: dict, integration: Union[AzureIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AzureIntegration):
            integration = AzureIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, integration: dict) -> dict:
        pass

    @staticmethod
    def get_forms():
        return {
            "label": "Azure",
            "type": "form",
            "children": [
                {
                    "label": "Service Principal Credentials",
                    "type": "form",
                    "children": [
                        {
                            "name": "tenant_id",
                            "type": "text",
                            "label": "Tenant ID",
                            "placeholder": "Enter your Azure tenant ID",
                            "required": True
                        },
                        {
                            "name": "client_id",
                            "type": "text",
                            "label": "Client ID",
                            "placeholder": "Enter your Azure application client ID",
                            "required": True
                        },
                        {
                            "name": "subscription_id",
                            "type": "text",
                            "label": "Subscription ID",
                            "placeholder": "Enter your Azure subscription ID",
                            "required": True
                        },
                        {
                            "name": "client_secret",
                            "type": "text",
                            "label": "Client Secret",
                            "placeholder": "Enter your Azure Application Client Seceret",
                        }
                    ]
                }
            ]
        }


    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AzureIntegration

    @classmethod
    def get_details(cls):
        return {
            "automation_supported": ["communication", 'mutation'],
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/azure.spc"
        config = """connection "azure" {
  plugin = "azure"

  subscription_id = "azure_01"

  ignore_error_codes = ["NoAuthenticationInformation", "InvalidAuthenticationInfo", "AccountIsDisabled", "UnauthorizedOperation", "UnrecognizedClientException", "AuthorizationError", "AuthenticationFailed", "InsufficientAccountPermissions"]
}"""
        return SteampipeCreds(envs=creds, plugin_name="azure", connection_name="azure",
                              conf_path=conf_path, config=config)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        clients_classes = dict()
        credential = ClientSecretCredential(
            tenant=self.integration.tenant_id,
            client_id=self.integration.client_id,
            client_secret=self.integration.client_secret
        )
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    clients_classes[client.class_name] = cls(credential)
            except BaseException as e:
                print(e)
                continue
        return [
            {
                "clients": clients_classes,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = self._temp_credentials()
        return SDKCreds(envs=creds)

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def _temp_credentials(self):
        return {
            "AZURE_TENANT_ID": self.integration.tenant_id,
            "AZURE_CLIENT_ID": self.integration.client_id,
            "AZURE_CLIENT_SECRET":self.integration.client_secret,
            "AZURE_SUBSCRIPTION_ID": self.integration.subscription_id,
        }
