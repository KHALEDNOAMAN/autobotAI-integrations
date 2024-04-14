import os
import importlib

from typing import List
from autobotAI_integrations import SDKClient
from kubernetes import config


class KubernetesHelper:

    def __init__(self, rctx, autobot_resources: bool = False, integration=None):
        self.ctx = rctx
        self.autobot_resources = autobot_resources
        self.csp = integration
    
    def get_kubernetes_config(self):
        """
        Determines and loads the appropriate Kubernetes configuration based on the environment.
        """

        in_cluster = os.getenv("KUBERNETES_SERVICE_ACCOUNT_TOKEN", "")  # Default to empty string
        if in_cluster:
            config.load_incluster_config()
            print("Loaded configuration from in-cluster service account.")
        else:
            config.load_kube_config()
            print("Loaded configuration from kubeconfig file.")

    def generate_clients(self, client_definitions):
        clients_classes = dict()
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    # In Kubernetes we are using client module which have enery class
                    # So here cls is reffered to "kubernetes.client"
                    clients_classes[client.name] = cls
            except BaseException as e:
                print(e)
                continue
        return clients_classes
