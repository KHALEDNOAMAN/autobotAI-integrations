import uuid
from typing import Dict, List, Type, Union
import os
import importlib
import json

from google.oauth2 import service_account
from pydantic import Field, field_validator
from functools import wraps

from autobotAI_integrations import list_of_unique_elements
from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient

from google.cloud.storage import Client as StorageClient
from google.oauth2.service_account import Credentials


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

    def model_dump_json(self, *args, **kwargs) -> str:
        kwargs["by_alias"] = True
        return super().model_dump_json(*args, **kwargs)


class GCPIntegration(BaseSchema):
    # TODO: Integration Credential Field Optimization
    account_id: Optional[str] = uuid.uuid4().hex
    credentials: GCPCredentials = Field(
        default=None, exclude=True
    )

    category: Optional[str] = IntegrationCategory.CLOUD_SERVICES_PROVIDERS.value
    description: Optional[str] = (
        "GCP is Google Cloud Platform, a suite of cloud computing services offered by Google."
    )

    def __init__(self, **kwargs):
        creds = kwargs.get("credentials")
        if isinstance(kwargs.get('credentials'), str):
            creds = json.loads(creds)
        kwargs["accountId"] = str(creds.get("project_id"))
        super().__init__(**kwargs)

    @property
    def credentials(self) -> dict:
        return self.credentials.model_dump(by_alias=True)

    def model_dump(self, *args, **kwargs) -> str:
        kwargs["by_alias"] = True
        return super().model_dump(*args, **kwargs)

    @field_validator('credentials', mode='before')
    @classmethod
    def validate_credentials(cls, credentials) -> GCPCredentials:
        if isinstance(credentials, str):
            try:
                return GCPCredentials(**json.loads(credentials))  # Parse JSON string
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid JSON format in 'credentials': {e}")
        return credentials


class GCPService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GCPIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GCPIntegration):
            integration = GCPIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            gcp_creds = self.integration.credentials.model_dump()
            credentials = Credentials.from_service_account_info(gcp_creds)
            client = StorageClient(credentials=credentials)
            buckets = client.list_buckets()
            print("Buckets: ")
            for bucket in buckets:
                print(bucket.name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "GCP",
            "type": "form",
            "children": [
                {
                    "label": "Service Account Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "credentials",
                            "type": "json",
                            "label": "Credentials JSON",
                            "placeholder": "Enter the Credentials In JSON Format",
                            "required": True,
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GCPIntegration

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
        conf_path = "~/.steampipe/config/gcp.spc"
        config = """connection "gcp" {
  plugin    = "gcp"

  ignore_error_codes = ["401", "403"]
}
"""
        return SteampipeCreds(
            envs=creds, plugin_name="gcp", connection_name="gcp", conf_path=conf_path, config=config,
        )

    def build_python_exec_combinations_hook(
            self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:

        clients_classes = dict()
        credentials = service_account.Credentials.from_service_account_info(payload_task.creds.envs["GOOGLE_APPLICATION_CREDENTIALS"])
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    clients_classes[client.name] = cls(
                        project=payload_task.creds.envs["CLOUDSDK_CORE_PROJECT"],
                        credentials=credentials
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
    def python_sdk_processor(self, payload_task: PayloadTask) -> (List[Dict[str, Any]], List[str]):  # type: ignore
        return super().python_sdk_processor(payload_task)

    @manage_creds_path
    def execute_steampipe_task(self, payload_task: PayloadTask):
        return super().execute_steampipe_task(payload_task)
