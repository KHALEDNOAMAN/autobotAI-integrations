import uuid
from typing import Dict, List
import importlib
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient, list_of_unique_elements
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.models import Dict


class KubernetesIntegration(BaseSchema):
    agent_ids: list = []
    connection_type: ConnectionTypes = ConnectionTypes.AGENT.value

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class KubernetesService(BaseService):
    def __init__(self, ctx, integration: KubernetesIntegration):
        # Assuming the cluster is alredy running in activate state
        super().__init__(ctx, integration)

    def get_forms(self):
        pass

    @staticmethod
    def get_schema():
        return KubernetesIntegration
    
    @classmethod
    def get_details(cls):
        return {
            "automation_code": "",
            "fetcher_code": "",
            "fetcher_supported": ["code"],
            "listener_supported": False,
            "automation_supported": ['mutation'],
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "compliance_supported": True
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def _test_integration(self, integration: dict):
        pass

    def _get_clients(self, client_definations: List[SDKClient]):
        client_classes = dict()
        for client in client_definations:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    client_classes[client.class_name] = cls
            except BaseException as e:
                print(e)
                continue
        return client_classes

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        clients = self._get_clients(client_definitions)
        return [
            {
                "clients": clients
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {}
        conf_path = "~/.steampipe/config/kubernetes.spc"
        return SteampipeCreds(
            envs=creds, plugin_name="kubernetes", connection_name="kubernetes", conf_path=conf_path
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds()

    def generate_cli_creds(self) -> CLICreds:
        return CLICreds()

