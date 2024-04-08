import uuid
from typing import Dict, List, Type, Union
import json
import os
from pydantic import Field
from functools import wraps
import importlib
import sys

from autobotAI_integrations import list_of_unique_elements
from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient


class GCPSDKClient(SDKClient):
    pass


class GCPCredentials(BaseModel):
    model_config = ConfigDict(frozen=True)

    type_: str = Field(alias="type")
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str


class GCPIntegration(BaseSchema):
    account_id: Optional[str] = uuid.uuid4().hex
    credentials: GCPCredentials = Field(
        default=None, exclude=True
    )  # Credentials Json of service account
    
    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GCPService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GCPIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GCPIntegration):
            integration = GCPIntegration(**integration)
        super().__init__(ctx, integration)
    
    def _test_integration(self, integration: dict) -> dict:
        pass

    def get_forms(self):
        return {
            "token_form": {
                "fields": [
                    {
                        "name": "credentials",
                        "type": "json",
                        "label": "Credentials JSON",
                        "placeholder": "Enter the Credentials In JSON Format",
                        "required": True,
                    },
                ],
                "submit_label": "Submit",
            }
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GCPIntegration

    @classmethod
    def get_details(cls):
        return {
            "automation_code": "",
            "fetcher_code": "",
            "automation_supported": ["communication", "mutation"],
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
        }

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/gcp.spc"
        return SteampipeCreds(
            envs=creds, plugin_name="gcp", connection_name="gcp", conf_path=conf_path
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
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
        return [
            {
                "clients": clients_classes
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        envs = self._temp_credentials()
        return SDKCreds(creds={}, envs=envs)

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def _temp_credentials(self):
        return {
            "CLOUDSDK_CORE_PROJECT": self.integration.credentials.project_id,
            "GOOGLE_APPLICATION_CREDENTIALS": self.integration.credentials.model_dump_json(by_alias=True)
        }
    
    def _get_creds_config_path(self):
        creds_path = f"gcp-creds-{uuid.uuid4().hex}.json"
        with open(creds_path, "w") as f:
            f.write(self.integration.credentials.model_dump_json(by_alias=True))
        return creds_path

    @staticmethod
    def manage_creds_path(func):
        @wraps(func)
        def wrapper(self, payload_task: PayloadTask, *args, **kwargs):
            creds_path = self._get_creds_config_path()
            try:
                if payload_task.creds and payload_task.creds.envs:
                    payload_task.creds.envs["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                return func(self, payload_task, *args, **kwargs)  # Call the original function
            finally:
                os.remove(creds_path)  # Ensure path is removed even if exceptions occur
        return wrapper

    @manage_creds_path
    def python_sdk_processor(self, payload_task: PayloadTask) -> (List[Dict[str, Any]], List[str]): # type: ignore
        return super().python_sdk_processor(payload_task)
    
    @manage_creds_path
    def execute_steampipe_task(self, payload_task: PayloadTask, job_type="query"):
        return super().execute_steampipe_task(payload_task, job_type)
