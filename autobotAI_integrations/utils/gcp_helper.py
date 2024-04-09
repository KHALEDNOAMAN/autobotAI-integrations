import os
import importlib

from google.oauth2.service_account import Credentials
from typing import List
from autobotAI_integrations import SDKClient

app_env = os.environ.get('APP_ENV', 'local')
run_env = os.environ.get('RUN_ENV', app_env)


class GCPHelper:

    def __init__(self, rctx, autobot_resources: bool = False, integration=None):
        self.ctx = rctx
        self.autobot_resources = autobot_resources
        self.csp = integration
    
    def get_credentials(self):
        credentials = Credentials.from_service_account_info(self.csp.credentials.model_dump())
        return credentials
    
    def generate_clients(self, client_definitions):
        clients_classes = dict()
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    clients_classes[client.class_name] = cls()
            except BaseException as e:
                print(e)
                continue
        return clients_classes

    def _get_session(self, cls):
        session = cls(credentials=self.get_credentials())
        return session

    def generate_clients_with_session(self, client_definations: List[SDKClient]):
        clients_classes = dict()
        for client in client_definations:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    clients_classes[client.class_name] = self._get_session(cls)
            except BaseException as e:
                print(e)
                continue
        return clients_classes
