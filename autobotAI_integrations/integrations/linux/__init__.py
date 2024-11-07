import uuid
from typing import Dict, List, Type, Union
import os
import importlib
from pydantic import Field
from functools import wraps

from autobotAI_integrations import list_of_unique_elements
from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from autobotAI_integrations.integration_schema import ConnectionTypes


class LinuxIntegration(BaseSchema):
    connection_type: ConnectionTypes = ConnectionTypes.AGENT.value
    category: Optional[str] = IntegrationCategory.AGENT_BASED.value
    description: Optional[str] = (
        "A free and open-source operating system widely used for servers, desktops, and embedded devices."
    )


class LinuxService(BaseService):

    def __init__(self, ctx: dict, integration: Union[LinuxIntegration, dict]):
        connection_type: ConnectionTypes = ConnectionTypes.AGENT.value
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, LinuxIntegration):
            integration = LinuxIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False) -> dict:
        try:
            import platform
            linux_version = platform.platform()
            print(f"Linux Distribution: {linux_version}")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e) }

    @staticmethod
    def get_forms():
        return {
            "label": "Linux Integration",
            "type": "form",
            "children": [
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return LinuxIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {}
        conf_path = "~/.steampipe/config/exec.spc"
        config = """connection "exec_local" {
  plugin = "exec"
}
"""
        return SteampipeCreds(
            envs=creds, plugin_name="exec", connection_name="exec", conf_path=conf_path, config=config,
        )

    def build_python_exec_combinations_hook(
            self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:

        clients_classes = dict()
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.import_library_names[0], package=None)
                clients_classes[client.name] = client_module
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
        envs = {}
        return SDKCreds(creds={}, envs=envs)

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()
