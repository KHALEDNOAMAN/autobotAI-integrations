import uuid
from typing import List
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient, list_of_unique_elements
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.utils import KubernetesHelper


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

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        k8s_helper = KubernetesHelper(self.ctx, self.integration)
        clients = k8s_helper.generate_clients(client_definitions)
        # Loading kubernet Config
        k8s_helper.get_kubernetes_config()
        return [
            {
                "clients": clients
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = self._temp_credentials()
        conf_path = "~/.steampipe/config/kubernetes.spc"
        return SteampipeCreds(
            envs=envs, plugin_name="kubernetes", connection_name="kubernetes", conf_path=conf_path
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = self._temp_credentials()
        return SDKCreds(envs=envs)

    def generate_cli_creds(self) -> CLICreds:
        envs = self._temp_credentials()
        return CLICreds(envs=envs)
    
    def _temp_credentials(self):
        return {
            "KUBECONFIG": "~/.kube/config"
        }

