from typing import Type, Union
from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements,PayloadTask
from autobotAI_integrations.models import *

import uuid

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

    def get_forms(self):
        return {}

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AzureIntegration

    @classmethod
    def get_details(cls):
        return {
            "automation_code": "",
            "fetcher_code": "",
            "automation_supported": ["communication", 'mutation'],
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/azure.spc"
        return SteampipeCreds(envs=creds, plugin_name="azure", connection_name="azure",
                              conf_path=conf_path)

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        pass

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
        pass
