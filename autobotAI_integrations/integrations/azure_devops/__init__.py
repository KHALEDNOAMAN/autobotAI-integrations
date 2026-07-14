import base64
import importlib
from typing import List, Optional, Union

import requests
from pydantic import Field, field_validator

from autobotAI_integrations import (
    BaseSchema,
    RestAPICreds,
    SDKCreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)
from autobotAI_integrations.models import IntegrationCategory


class AzureDevOpsIntegration(BaseSchema):
    base_url: str = Field(
        default="https://dev.azure.com",
        description="Base URL of Azure DevOps server/service",
    )
    organization: Optional[str] = Field(
        default=None,
        description="Azure DevOps organization name (e.g., 'myorg' for cloud https://dev.azure.com/myorg)",
    )
    personal_access_token: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Personal Access Token (PAT) with required scopes",
    )
    client_id: Optional[str] = Field(
        default=None,
        description="Azure AD / Entra ID Application (Client) ID (if using Service Principal auth instead of PAT)",
    )
    client_secret: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Azure AD / Entra ID Client Secret (if using Service Principal auth instead of PAT)",
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Azure AD / Entra ID Directory (Tenant) ID (if using Service Principal auth instead of PAT)",
    )

    name: Optional[str] = "Azure DevOps"
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        "Azure DevOps provides developer services for support teams to plan work, collaborate on code development, and build and deploy applications."
    )

    def __init__(self, **kwargs):
        # If organization is provided, use it as accountId fallback if accountId is not explicitly set.
        if kwargs.get("organization"):
            kwargs.setdefault("accountId", kwargs["organization"])
        kwargs.setdefault("cspName", "AZURE_DEVOPS")
        kwargs.setdefault("alias", kwargs.get("organization") or "Azure DevOps")
        super().__init__(**kwargs)

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v):
        if v is None or v.strip() == "":
            return "https://dev.azure.com"
        return v.rstrip("/")


class AzureDevOpsService(BaseService):
    def __init__(self, ctx: dict, integration: Union[AzureDevOpsIntegration, dict]):
        """
        Integration should have all the data regarding the integration.
        """
        if not isinstance(integration, AzureDevOpsIntegration):
            integration = AzureDevOpsIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_organization_url(self) -> str:
        """
        Helper method to construct the full Azure DevOps organization or server URL.
        """
        base = (self.integration.base_url or "https://dev.azure.com").rstrip("/")
        org = (self.integration.organization or "").strip().strip("/")
        if org:
            if base.lower().endswith(f"/{org.lower()}"):
                return base
            if base.lower() != "https://dev.azure.com":
                return f"{base}/{org}"
            return f"https://dev.azure.com/{org}"
        return base

    def _get_auth_header(self) -> str:
        """
        Helper method to get Authorization header string (`Basic <b64>` for PAT or `Bearer <token>` for Service Principal).
        """
        if self.integration.personal_access_token:
            auth_str = f":{self.integration.personal_access_token}"
            return "Basic " + base64.b64encode(auth_str.encode()).decode()

        if (
            self.integration.client_id
            and self.integration.client_secret
            and self.integration.tenant_id
        ):
            token_url = f"https://login.microsoftonline.com/{self.integration.tenant_id.strip()}/oauth2/v2.0/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.integration.client_id.strip(),
                "client_secret": self.integration.client_secret.strip(),
                "scope": "499b84ac-1321-427f-aa17-267ca6975798/.default",
            }
            resp = requests.post(token_url, data=data, timeout=15)
            if resp.status_code == 200:
                token_data = resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    raise ValueError("OAuth token response did not contain an access_token field.")
                return f"Bearer {access_token}"
            else:
                raise ValueError(
                    f"Failed to obtain OAuth token from Entra ID ({resp.status_code}): {resp.text}"
                )

        raise ValueError(
            "Either Personal Access Token (PAT) OR complete Service Principal credentials (Client ID, Client Secret, Tenant ID) must be provided."
        )

    def _test_integration(self) -> dict:
        """
        Tests connectivity and authentication against Azure DevOps REST API using either PAT or Service Principal.
        """
        org_url = self._get_organization_url()
        endpoint = f"{org_url}/_apis/projects?top=1&api-version=7.1"

        try:
            auth_header = self._get_auth_header()

            response = requests.get(
                endpoint,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                },
                timeout=15,
            )

            if response.status_code in [200, 203]:
                return {"success": True}
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid PAT or Service Principal credentials (Unauthorized).",
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Azure DevOps organization or endpoint not found: {org_url}",
                }
            else:
                return {
                    "success": False,
                    "error": f"Unexpected status code {response.status_code}. Response: {response.text}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms() -> dict:
        return {
            "label": "Azure DevOps",
            "type": "form",
            "children": [
                {
                    "name": "organization",
                    "type": "text",
                    "label": "Organization Name",
                    "placeholder": "e.g., myorg (leave blank if using custom base_url with collection path)",
                    "description": "The Azure DevOps organization name (cloud: https://dev.azure.com/{organization}).",
                    "required": False,
                },
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Base URL",
                    "placeholder": "https://dev.azure.com",
                    "default_value": "https://dev.azure.com",
                    "description": "Base URL of Azure DevOps server/service. Use https://dev.azure.com for cloud, or custom URL for Azure DevOps Server/On-Premises.",
                    "required": False,
                },
                {
                    "name": "personal_access_token",
                    "type": "text/password",
                    "label": "Personal Access Token (PAT)",
                    "placeholder": "Enter your Azure DevOps PAT",
                    "description": "Personal Access Token with required scopes (Code Read/Write, Work Items Read/Write, Build Read/Execute). Optional if using Service Principal below.",
                    "required": False,
                },
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Application (Client) ID",
                    "placeholder": "Enter your Azure AD / Entra ID Client ID",
                    "description": "Service Principal Client ID (Optional: use only if authenticating via Service Principal instead of PAT).",
                    "required": False,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Azure AD / Entra ID Client Secret",
                    "description": "Service Principal Client Secret value (Optional: use only if authenticating via Service Principal instead of PAT).",
                    "required": False,
                },
                {
                    "name": "tenant_id",
                    "type": "text",
                    "label": "Directory (Tenant) ID",
                    "placeholder": "Enter your Azure AD / Entra ID Tenant ID",
                    "description": "Service Principal Tenant ID (Optional: use only if authenticating via Service Principal instead of PAT).",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return AzureDevOpsIntegration

    @staticmethod
    def supported_connection_interfaces() -> list:
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        azure_devops_conn = importlib.import_module("azure.devops.connection", package=None)
        ConnectionClass = getattr(azure_devops_conn, "Connection")

        envs = getattr(payload_task.creds, "envs", None) or {}
        org_url = (
            envs.get("AZURE_DEVOPS_ORG_URL")
            or envs.get("AZURE_DEVOPS_BASE_URL")
            or getattr(payload_task.creds, "base_url", None)
            or self._get_organization_url()
        )
        pat = (
            envs.get("AZURE_DEVOPS_PAT")
            or self.integration.personal_access_token
            or ""
        )

        if pat:
            msrest_auth = importlib.import_module("msrest.authentication", package=None)
            BasicAuthenticationClass = getattr(msrest_auth, "BasicAuthentication")
            credentials = BasicAuthenticationClass("", pat)
        else:
            auth_header = self._get_auth_header()
            token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else auth_header
            msrest_auth = importlib.import_module("msrest.authentication", package=None)
            BasicTokenAuthenticationClass = getattr(msrest_auth, "BasicTokenAuthentication", None)
            if BasicTokenAuthenticationClass:
                credentials = BasicTokenAuthenticationClass({"access_token": token})
            else:
                BasicAuthenticationClass = getattr(msrest_auth, "BasicAuthentication")
                credentials = BasicAuthenticationClass("", token)

        connection = ConnectionClass(base_url=org_url, creds=credentials)

        return [
            {
                "clients": {"azure_devops": connection},
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        org_url = self._get_organization_url()
        auth_header = self._get_auth_header()

        return RestAPICreds(
            base_url=org_url,
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        org_url = self._get_organization_url()
        pat = self.integration.personal_access_token or ""
        return SDKCreds(
            envs={
                "AZURE_DEVOPS_ORG_URL": org_url,
                "AZURE_DEVOPS_BASE_URL": org_url,
                "AZURE_DEVOPS_PAT": pat,
                "AZURE_DEVOPS_CLIENT_ID": self.integration.client_id or "",
                "AZURE_DEVOPS_CLIENT_SECRET": self.integration.client_secret or "",
                "AZURE_DEVOPS_TENANT_ID": self.integration.tenant_id or "",
            }
        )
