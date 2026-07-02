import importlib
from typing import List, Optional, Type, Union

import requests
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    RestAPICreds,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.models import IntegrationCategory

GRAPH_BASE_URL = "https://graph.microsoft.com"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


class M365DLPIntegration(BaseSchema):
    tenant_id: Optional[str] = Field(default=None, description="Microsoft Tenant ID")
    client_id: Optional[str] = Field(default=None, description="Microsoft Client ID", exclude=True)
    client_secret: Optional[str] = Field(
        default=None, description="Microsoft Client Secret", exclude=True
    )

    name: str = "Microsoft 365 DLP"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Microsoft Purview Data Loss Prevention (DLP) for Microsoft 365. "
        "Monitor DLP alerts, audit activity, sensitive information types, and "
        "investigate policy matches across Exchange, SharePoint, OneDrive, Teams, "
        "and Endpoint DLP using Microsoft Graph APIs."
    )


class M365DLPService(BaseService):
    def __init__(self, ctx: dict, integration: Union[M365DLPIntegration, dict]):
        if not isinstance(integration, M365DLPIntegration):
            integration = M365DLPIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_access_token(self) -> str:
        url = (
            f"https://login.microsoftonline.com/{self.integration.tenant_id}"
            "/oauth2/v2.0/token"
        )
        response = requests.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": self.integration.client_id,
                "scope": GRAPH_SCOPE,
                "client_secret": self.integration.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=15,
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

    def _test_integration(self) -> dict:
        try:
            token = self._get_access_token()
            response = requests.get(
                f"{GRAPH_BASE_URL}/v1.0/security/alerts_v2",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                params={"$top": 1},
                timeout=15,
            )
            if response.status_code == 200:
                return {"success": True}
            if response.status_code in (401, 403):
                return {
                    "success": False,
                    "error": (
                        "Authentication failed or insufficient Graph permissions. "
                        "Ensure the app has SecurityAlert.Read.All and related "
                        "Purview audit permissions."
                    ),
                }
            return {
                "success": False,
                "error": (
                    f"DLP API check failed ({response.status_code}): "
                    f"{response.text[:300]}"
                ),
            }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is unreachable"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Authentication failed: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Microsoft 365 DLP",
            "type": "form",
            "children": [
                {
                    "name": "tenant_id",
                    "type": "text",
                    "label": "Tenant ID",
                    "placeholder": "Enter your Microsoft tenant ID",
                    "description": (
                        "Azure AD tenant ID for your Microsoft 365 organization."
                    ),
                    "required": True,
                    "help_url": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    "help_url_text": "Get Tenant ID ↗",
                },
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter your Microsoft application client ID",
                    "description": (
                        "App registration with Microsoft Graph application permissions "
                        "such as SecurityAlert.Read.All, SecurityAlert.ReadWrite.All, "
                        "and AuditLogsQuery.Read.All."
                    ),
                    "required": True,
                    "help_url": "https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    "help_url_text": "Get Client ID ↗",
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Microsoft application client secret",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return M365DLPIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        token = self._get_access_token()
        return RestAPICreds(
            base_url=GRAPH_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            envs={
                "AZURE_TENANT_ID": self.integration.tenant_id,
                "AZURE_CLIENT_ID": self.integration.client_id,
                "AZURE_CLIENT_SECRET": self.integration.client_secret,
            }
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        from azure.identity import ClientSecretCredential

        credential = ClientSecretCredential(
            tenant_id=payload_task.creds.envs.get("AZURE_TENANT_ID"),
            client_id=payload_task.creds.envs.get("AZURE_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("AZURE_CLIENT_SECRET"),
        )
        scopes = [GRAPH_SCOPE]
        msgraph = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        return [
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
