from typing import List, Type, Union
import importlib
import json

from pydantic import field_validator
import urllib.parse

from autobotAI_integrations.models import *
from autobotAI_integrations.models import List, SDKCreds
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    SDKCreds,
    SteampipeCreds,
    PayloadTask,
    SDKClient,
)

from google.oauth2.service_account import Credentials
from autobotAI_integrations.integrations.gcp import GCPCredentials, GCPService, GCPIntegration
import uuid


class GoogleAPIsIntegration(GCPIntegration):
    scopes: List[str] = []
    user_email: Optional[str] = None

    name: Optional[str] = "Google APIs"
    description: Optional[str] = (
        "Google APIs are a set of tools that allow developers to programmatically access and interact with Google's services and data."
    )

    def __init__(self, **kwargs):
        if not kwargs.get("accountId"):
            kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)

    @field_validator("scopes", mode="before")
    @classmethod
    def validate_scopes(cls, scopes) -> List[str]:
        validated_scopes = []
        if isinstance(scopes, list):
            return scopes
        elif isinstance(scopes, str):
            scopes = scopes.split(", ")
            for scope in scopes:
                decoded_url = urllib.parse.unquote(scope)
                cleaned_url = decoded_url.replace("\n", "")
                scope = cleaned_url.strip()
                if scope.startswith("https://"):
                    validated_scopes.append(scope)
                else:
                    raise ValueError("Invalid scope format")
        if len(validated_scopes) == 0:
            raise ValueError("At least one valid scope is required")
        return validated_scopes


class GoogleAPIsService(GCPService, BaseService):

    def __init__(self, ctx: dict, integration: Union[GoogleAPIsIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GoogleAPIsIntegration):
            integration = GoogleAPIsIntegration(**integration)
        super().__init__(ctx, integration)

    @staticmethod
    def get_forms():
        return {
            "label": "Google APIs",
            "type": "form",
            "children": [
                {
                    "name": "scopes",
                    "type": "textarea",
                    "label": "Scopes",
                    "placeholder": "https://www.googleapis.com/auth/gmail.readonly, https://www.googleapis.com/auth/drive",
                    "description": "Enter multiple OAuth scopes as comma-separated values. Example: https://www.googleapis.com/auth/gmail.readonly, https://www.googleapis.com/auth/drive",
                    "required": True,
                },
                {
                    "name": "user_email",
                    "type": "text",
                    "label": "User Email",
                    "placeholder": "username@domain.com",
                    "description": "Enter the email of the user to be impersonated by the service account. This must be a valid user in your Google Workspace domain.",
                    "required": True,
                },
                {
                    "name": "credentials",
                    "type": "json",
                    "label": "Credentials JSON",
                    "placeholder": "Enter the Credentials In JSON Format",
                    "description": "Upload the service account Credentials JSON file obtained from Google Cloud Console.",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GoogleAPIsIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["compliance_supported"] = False
        return details

    #     def generate_steampipe_creds(self) -> SteampipeCreds:
    #         creds = self._temp_credentials()
    #         conf_path = "(~/.steampipe/config/googleworkspace.spc"
    #         config = f"""connection "googleworkspace" {{
    #   plugin = "googleworkspace"
    #   impersonated_user_email = "{self.integration.user_email}"

    # }}
    # """
    #         return SteampipeCreds(
    #             envs=creds,
    #             plugin_name="googleworkspace",
    #             connection_name="googleworkspace",
    #             conf_path=conf_path,
    #             config=config,
    #         )

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        raise NotImplementedError()

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:

        clients_classes = dict()
        credentials_dict = GCPCredentials.model_validate_json(
            json.loads(payload_task.creds.envs["GOOGLE_APPLICATION_CREDENTIALS"])
        ).model_dump()

        scopes = payload_task.creds.envs["GOOGLE_APPLICATION_SCOPES"].split(",")
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        if payload_task.creds.envs.get("IMPERSONATED_USER_EMAIL"):
            credentials = credentials.with_subject(
                payload_task.creds.envs["IMPERSONATED_USER_EMAIL"]
            )
        for client in client_definitions:
            try:
                discovery = importlib.import_module(client.module, package=None)
                name, version = client.name.split("_")
                clients_classes[client.name] = discovery.build(
                    serviceName=name,
                    version=version,
                    credentials=credentials,
                )
            except BaseException as e:
                print(e)
                continue
        return [
            {
                "clients": clients_classes,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        envs = super()._temp_credentials()
        envs["GOOGLE_APPLICATION_SCOPES"] = ",".join(self.integration.scopes)
        envs["IMPERSONATED_USER_EMAIL"] = self.integration.user_email
        return SDKCreds(creds={}, envs=envs)
