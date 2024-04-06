import uuid
from typing import Type, Union

from pydantic import Field

from autobotAI_integrations import BaseService, list_of_unique_elements, PayloadTask
from autobotAI_integrations.models import *


class GCPSDKClient(SDKClient):
    pass


class GCPCredentials(BaseModel):
    credential_type: str = Field(..., alias="type")
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str

    class Config:
        allow_mutation = False  # Disallows mutation of the model


class GCPIntegration(BaseSchema):
    account_id: Optional[str] = None
    project_id: Optional[str] = None  # If not provided fetch the active project ID
    credentials: GCPCredentials = Field(
        default=None, exclude=True
    )  # Credentials Json of service account
    service_account: Optional[str] = None  # Optional impersonate_service_account
    quata_project_id: Optional[str] = None  # The project ID used for billing and quota. When set

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
                        "name": "project_id",
                        "type": "text",
                        "label": "Project ID",
                        "required": True,
                    },
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
        pass

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        pass

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
        pass
