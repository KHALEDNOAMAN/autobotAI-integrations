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

from .scm_client import PaloAltoSCMClient


class PaloAltoSCMIntegration(BaseSchema):
    auth_url: str = Field(
        default="https://auth.apps.paloaltonetworks.com/oauth2/access_token"
    )
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    host: str = Field(default="api.strata.paloaltonetworks.com")
    protocol: str = Field(default="https")
    scope: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Palo Alto Strata Cloud Manager"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Palo Alto Networks Strata Cloud Manager (SCM) provides centralized "
        "configuration and management for next-generation firewalls and "
        "Prisma Access via the Strata Cloud Manager APIs."
    )


class PaloAltoSCMService(BaseService):
    def __init__(self, ctx: dict, integration: Union[PaloAltoSCMIntegration, dict]):
        if not isinstance(integration, PaloAltoSCMIntegration):
            integration = PaloAltoSCMIntegration(**integration)
        super().__init__(ctx, integration)

    def _base_url(self) -> str:
        return f"{self.integration.protocol.rstrip(':/')}://{self.integration.host.strip('/')}"

    def _get_access_token(self) -> str:
        """
        Generate an OAuth2 access token for SCM using client_credentials.
        """
        response = requests.post(
            self.integration.auth_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "client_credentials",
                "client_id": self.integration.client_id,
                "client_secret": self.integration.client_secret,
                "scope": self.integration.scope,
            },
            timeout=30,
        )
        if not response.ok:
            raise requests.exceptions.HTTPError(
                f"{response.status_code} - {response.text}",
                response=response,
            )
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Token response did not contain an access_token")
        return access_token

    def _test_integration(self) -> dict:
        try:
            token = self._get_access_token()
            if not token:
                return {
                    "success": False,
                    "error": "Token generation succeeded but access_token was missing in response.",
                }

            response = requests.get(
                f"{self._base_url()}/config/setup/v1/devices",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            if response.status_code == 200:
                return {"success": True}
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
            }
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Authentication failed: {e}"}
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection is unreachable. Verify host, protocol, and auth_url.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Palo Alto Strata Cloud Manager",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text/password",
                    "label": "Client ID",
                    "placeholder": "Enter your SCM OAuth Client ID",
                    "description": "Service account Client ID from Strata Cloud Manager Identity & Access.",
                    "required": True,
                    "help_url": "https://pan.dev/scm/docs/getstarted/",
                    "help_url_text": "SCM API Docs ↗",
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your SCM OAuth Client Secret",
                    "required": True,
                },
                {
                    "name": "scope",
                    "type": "text",
                    "label": "Scope",
                    "placeholder": "tsg_id:<YOUR_TSG_ID>",
                    "description": "OAuth scope in the form tsg_id:<Tenant Service Group ID>.",
                    "required": True,
                },
                {
                    "name": "auth_url",
                    "type": "text/url",
                    "label": "Auth URL",
                    "placeholder": "https://auth.apps.paloaltonetworks.com/oauth2/access_token",
                    "description": "OAuth2 token endpoint. Override only if your environment uses a different auth host.",
                    "required": False,
                    "default": "https://auth.apps.paloaltonetworks.com/oauth2/access_token",
                },
                {
                    "name": "host",
                    "type": "text",
                    "label": "API Host",
                    "placeholder": "api.strata.paloaltonetworks.com",
                    "description": "SCM API hostname without protocol.",
                    "required": False,
                    "default": "api.strata.paloaltonetworks.com",
                },
                {
                    "name": "protocol",
                    "type": "select",
                    "label": "Protocol",
                    "placeholder": "https",
                    "description": "HTTP protocol used to reach the SCM API.",
                    "required": False,
                    "options": [
                        {"label": "https", "value": "https"},
                        {"label": "http", "value": "http"},
                    ],
                    "default": "https",
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return PaloAltoSCMIntegration

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
            base_url=self._base_url(),
            token=token,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        return SDKCreds(
            envs={
                "PALO_ALTO_SCM_AUTH_URL": str(self.integration.auth_url),
                "PALO_ALTO_SCM_CLIENT_ID": str(self.integration.client_id),
                "PALO_ALTO_SCM_CLIENT_SECRET": str(self.integration.client_secret),
                "PALO_ALTO_SCM_HOST": str(self.integration.host),
                "PALO_ALTO_SCM_PROTOCOL": str(self.integration.protocol),
                "PALO_ALTO_SCM_SCOPE": str(self.integration.scope),
            }
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        envs = payload_task.creds.envs or {}
        client = PaloAltoSCMClient(
            protocol=envs.get("PALO_ALTO_SCM_PROTOCOL", "https"),
            host=envs.get("PALO_ALTO_SCM_HOST", "api.strata.paloaltonetworks.com"),
            auth_url=envs.get(
                "PALO_ALTO_SCM_AUTH_URL",
                "https://auth.apps.paloaltonetworks.com/oauth2/access_token",
            ),
            client_id=envs.get("PALO_ALTO_SCM_CLIENT_ID"),
            client_secret=envs.get("PALO_ALTO_SCM_CLIENT_SECRET"),
            scope=envs.get("PALO_ALTO_SCM_SCOPE"),
        )
        return [
            {
                "clients": {"palo_alto_scm": client},
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
