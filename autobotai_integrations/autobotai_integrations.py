import os
import subprocess
import sys
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from pydantic import BaseModel
from autobotai_integrations.integration_schema import IntegrationSchema


class AuthMethods(Enum):
    STEAMPIPE = 'steampipe'
    PYTHON_SDK = 'python_sdk'
    REST_API = 'rest_api'
    CLI = 'cli'


class SteampipeCreds(BaseModel):
    envs: dict
    connection_name: str
    plugin_name: str
    conf_path: Optional[str] = str
    tables: list = []


class RestAPICreds(BaseModel):
    api_url: str
    token: str
    headers: str


class SDKCreds(BaseModel):
    clients: Dict[str, Any]
    library_names: List[str]
    package_names: List[str]
    creds: Optional[dict] = None
    envs: Optional[dict] = None


class CLICreds(BaseModel):
    envs: dict
    installer_check: str
    install_command: str


class BaseSchema(IntegrationSchema):
    name: str
    description: str
    logo: str
    authentication_methods: List[AuthMethods] = []
    creds: Optional[Any] = None


class BaseService:

    def __init__(self, integration: dict):
        pass

    @staticmethod
    def get_schema() -> BaseSchema:
        raise NotImplementedError()

    # TODO: Generate accountId if not given
    def generate_steampipe_creds(self) -> SteampipeCreds:
        raise NotImplementedError()

    def generate_rest_api_creds(self) -> RestAPICreds:
        raise NotImplementedError()

    def generate_python_sdk_creds(self) -> SDKCreds:
        raise NotImplementedError()

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    """
    Callable in python_sdk_processor means this ->

    @staticmethod
    def exec(clients: Dict[str, Any], resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass

    """

    @staticmethod
    def python_sdk_processor(code_exec: Callable[[Dict[str, Any], List[Dict[str, Any]]], List[Dict[str, Any]]],
                             resources: list, clients: list, creds: SDKCreds):
        # Setup Environment Variables
        for key, value in creds.envs.items():
            os.environ[key] = value

        # Install Packages
        for package_name in creds.package_names:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

        # Import Packages
        for library_name in creds.library_names:
            exec(f"import {library_name}")

        # Create Clients
        clients_to_run = {}
        for client in clients:
            clients_to_run[client] = eval(creds.clients[client]["code"])

        # Run the code and return Results
        results = code_exec(clients_to_run, resources)
        return results
