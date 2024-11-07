from typing import Type, Union
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements,PayloadTask
from autobotAI_integrations.models import *

import uuid
import importlib

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient


class AzureIntegration(BaseSchema):
    tenant_id: Optional[str] = Field(default=None, exclude=True)
    client_id: Optional[str] = Field(default=None, exclude=True)
    subscription_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Azure"
    category: Optional[str] = IntegrationCategory.CLOUD_SERVICES_PROVIDERS.value
    description: Optional[str] = (
        "Azure is a cloud computing platform developed by Microsoft that provides a wide range of services for building, deploying, and managing applications on a global scale."
    )

    def __init__(self, **kwargs):
        if kwargs.get("subscription_id"):
            kwargs["accountId"] = kwargs["subscription_id"]
        super().__init__(**kwargs)


class AzureService(BaseService):

    def __init__(self, ctx: dict, integration: Union[AzureIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AzureIntegration):
            integration = AzureIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            credentials = ClientSecretCredential(
                tenant_id=self.integration.tenant_id,
                client_id=self.integration.client_id,
                client_secret=self.integration.client_secret
            )
            client = ResourceManagementClient(credential=credentials, subscription_id=self.integration.subscription_id)
            resources = list(client.resources.list())
            return {"success": True}
        except Exception as e:
            # Custom one line error message
            return {"success": False, "error": str(e).split(".")[0]}

    @staticmethod
    def get_forms():
        return {
            "label": "Azure",
            "type": "form",
            "children": [
                {
                    "name": "tenant_id",
                    "type": "text",
                    "label": "Tenant ID",
                    "placeholder": "Enter your Azure tenant ID",
                    "required": True,
                },
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter your Azure application client ID",
                    "required": True,
                },
                {
                    "name": "subscription_id",
                    "type": "text",
                    "label": "Subscription ID",
                    "placeholder": "Enter your Azure subscription ID",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Azure Application Client Secret",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AzureIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": True,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/azure.spc"
        config = """connection "azure" {
  plugin = "azure"

  ignore_error_codes = ["NoAuthenticationInformation", "InvalidAuthenticationInfo", "AccountIsDisabled", "UnauthorizedOperation", "UnrecognizedClientException", "AuthorizationError", "AuthenticationFailed", "InsufficientAccountPermissions"]
}"""
        return SteampipeCreds(envs=creds, plugin_name="azure", connection_name="azure",
                              conf_path=conf_path, config=config)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        clients_classes = dict()
        credential = ClientSecretCredential(
            tenant_id=payload_task.creds.envs.get("AZURE_TENANT_ID"),
            client_id=payload_task.creds.envs.get("AZURE_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("AZURE_CLIENT_SECRET"),
        )
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    try:
                        clients_classes[client.class_name] = cls(
                            credential=credential,
                            subscription_id=payload_task.creds.envs.get("AZURE_SUBSCRIPTION_ID"),
                        )
                    except BaseException as e:
                        clients_classes[client.class_name] = cls(
                            credential=credential
                        )
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
