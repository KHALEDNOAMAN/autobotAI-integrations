from autobotAI_integrations import CLICreds, list_of_unique_elements
import importlib
from typing import List, Optional, Type, Union
from autobotAI_integrations import (
    BaseService,
    BaseSchema,
    RestAPICreds,
    SDKCreds,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)
from pydantic import Field
from autobotAI_integrations.models import IntegrationCategory
import requests

DEFENDER_XDR_BASE_URL = "https://api.security.microsoft.com"


class MicrosoftDefenderIntegration(BaseSchema):
    tenant_id: Optional[str] = Field(default=None, description="Microsoft Tenant ID")
    client_id: Optional[str] = Field(default=None, description="Microsoft Client ID", exclude=True)
    client_secret: Optional[str] = Field(
        default=None, description="Microsoft Client Secret", exclude=True
    )
    name: Optional[str] = "Microsoft Defender for Office 365"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Microsoft Defender for Office 365 is a cloud-based security service that protects "
        "organizations from malicious cyberthreats. It automatically filters out and blocks "
        "dangerous emails, links, and attachments across corporate inboxes and communication "
        "platforms like Microsoft Teams."
    )
    

class MicrosoftDefenderService(BaseService):
    def __init__(
        self, ctx: dict, integration: Union[MicrosoftDefenderIntegration, dict]
    ):
        if not isinstance(integration, MicrosoftDefenderIntegration):
            integration = MicrosoftDefenderIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            self._get_access_token("https://api.security.microsoft.com/.default")
            return {"success": True}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Authentication failed: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Microsoft Defender",
            "type": "form",
            "children": [
                {
                    "name": "tenant_id",
                    "type": "text",
                    "label": "Tenant ID",
                    "placeholder": "Enter your Microsoft tenant ID",
                    "required": True,
                    "help_url": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    "help_url_text": "Get Tenant ID ↗",
                },
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter your Microsoft application client ID",
                    "required": True,
                    "help_url": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    "help_url_text": "Get Client ID ↗",
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Microsoft Application Client Secret",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return MicrosoftDefenderIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    def _get_access_token(self, scope: str) -> str:
        url = (
            f"https://login.microsoftonline.com/{self.integration.tenant_id}"
            "/oauth2/v2.0/token"
        )
        response = requests.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": self.integration.client_id,
                "scope": scope,
                "client_secret": self.integration.client_secret,
                "grant_type": "client_credentials",
            },
        )
        if not response.ok:
            raise requests.exceptions.HTTPError(
                f"Token request failed ({response.status_code}): {response.text}",
                response=response,
            )
        token = response.json().get("access_token")
        if not token:
            raise ValueError("Token response did not contain an access_token")
        return token

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        # Ref: https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.clientsecretcredential
        # ClientSecretCredential(tenant_id, client_id, client_secret) — subscription_id is NOT
        # a credential parameter; it is passed to management-plane clients separately when needed.
        from azure.identity import ClientSecretCredential

        credential = ClientSecretCredential(
            tenant_id=payload_task.creds.envs.get("AZURE_TENANT_ID"),
            client_id=payload_task.creds.envs.get("AZURE_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("AZURE_CLIENT_SECRET"),
        )
        scopes = ["https://graph.microsoft.com/.default"]
        msgraph = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        item = [
            {
                "clients": {
                    "msgraph": msgraph.GraphServiceClient(
                        credentials=credential, scopes=scopes
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
        try:
            defender_scopes = ["https://api.security.microsoft.com/.default"]
            defender_client = msgraph.GraphServiceClient(
            credentials=credential, scopes=defender_scopes
        )
            item[0]["clients"]["msgraph-defender"] = defender_client
        except:
            pass
        return item

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "AZURE_TENANT_ID": self.integration.tenant_id,
            "AZURE_CLIENT_ID": self.integration.client_id,
            "AZURE_CLIENT_SECRET": self.integration.client_secret,
        }
        return SDKCreds(envs=envs)

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        token = self._get_access_token("https://api.security.microsoft.com/.default")
        return RestAPICreds(
            base_url=DEFENDER_XDR_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def _temp_credentials(self) -> dict:
        return {
            "AZURE_TENANT_ID": self.integration.tenant_id,
            "AZURE_CLIENT_ID": self.integration.client_id,
            "AZURE_CLIENT_SECRET": self.integration.client_secret,
        }