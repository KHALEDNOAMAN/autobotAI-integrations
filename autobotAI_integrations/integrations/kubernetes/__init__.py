import uuid
from typing import List, Optional
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient, list_of_unique_elements
from autobotAI_integrations.integration_schema import ConnectionTypes
import importlib
from kubernetes import config

from autobotAI_integrations.models import IntegrationCategory

class KubernetesIntegration(BaseSchema):
    agent_ids: list = []
    connection_type: ConnectionTypes = ConnectionTypes.AGENT.value

    category: Optional[str] = IntegrationCategory.AGENT_BASED.value
    description: Optional[str] = (
        "An orchestration system for managing containerized applications. It automates deployment, scaling, and management of containerized workloads."
    )


class KubernetesService(BaseService):
    def __init__(self, ctx, integration: KubernetesIntegration):
        # Assuming the cluster is alredy running in activate state
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return  {
            "label": "Kubernetes",
            "type": "form",
            "children": []
        }

    @staticmethod
    def get_schema():
        return KubernetesIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": True,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def _test_integration(self):
        return {"success": True}

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        kubernetes = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        try:
            config.load_kube_config()
        except:
            try:
                config.load_incluster_config()
            except:
                raise BaseException("Failed to load configurations")
        return [
            {
                "clients": {
                    "kubernetes": kubernetes,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = self._temp_credentials()
        conf_path = "~/.steampipe/config/kubernetes.spc"
        config = """connection "kubernetes" {
  plugin         = "kubernetes"
  config_path    = "~/.kube/config"
}"""
        return SteampipeCreds(
            envs=envs, plugin_name="kubernetes", connection_name="kubernetes", conf_path=conf_path, config=config
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
