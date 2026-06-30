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

CLOUD_BASE_URLS = {
    "us-1": "https://api.crowdstrike.com",
    "us-2": "https://api.us-2.crowdstrike.com",
    "eu-1": "https://api.eu-1.crowdstrike.com",
    "us-gov-1": "https://api.laggar.gcw.crowdstrike.com",
}


def _get_base_url(client_cloud: str) -> str:
    return CLOUD_BASE_URLS.get(client_cloud, CLOUD_BASE_URLS["us-2"])


def _get_token(client_id: str, client_secret: str, client_cloud: str) -> str:
    base_url = _get_base_url(client_cloud)
    response = requests.post(
        f"{base_url}/oauth2/token",
        data={"client_id": client_id, "client_secret": client_secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not response.ok:
        raise requests.exceptions.HTTPError(
            f"OAuth2 token request failed ({response.status_code}): {response.text}",
            response=response,
        )
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise ValueError("Token response did not contain an access_token")
    return access_token


class CrowdstrikeIdentityProtectionIntegration(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    client_cloud: Optional[str] = Field(default="us-2", exclude=True)

    name: Optional[str] = "CrowdStrike Identity Protection"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CrowdStrike Falcon Identity Protection provides identity threat detection, "
        "entity visibility, zero trust assessment, and policy-based response for "
        "identity-based attacks across your environment."
    )


class CrowdstrikeIdentityProtectionService(BaseService):

    def __init__(
        self,
        ctx: dict,
        integration: Union[CrowdstrikeIdentityProtectionIntegration, dict],
    ):
        if not isinstance(integration, CrowdstrikeIdentityProtectionIntegration):
            integration = CrowdstrikeIdentityProtectionIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            token = _get_token(
                client_id=self.integration.client_id,
                client_secret=self.integration.client_secret,
                client_cloud=self.integration.client_cloud,
            )
            base_url = _get_base_url(self.integration.client_cloud)
            response = requests.get(
                f"{base_url}/identity-protection/queries/devices/v1",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                params={"limit": 1},
            )
            if response.status_code < 400:
                return {"success": True}
            return {
                "success": False,
                "error": (
                    f"Identity Protection API check failed "
                    f"({response.status_code}): {response.text[:300]}"
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
            "label": "CrowdStrike Identity Protection",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter the Falcon API Client ID",
                    "description": (
                        "API Client ID with Identity Protection scopes "
                        "(e.g. Identity Protection Entities, Identity Protection GraphQL)"
                    ),
                    "required": True,
                    "help_url": "https://falcon.crowdstrike.com/support/api-clients-and-keys",
                    "help_url_text": "Get Client ID ↗",
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter the Falcon API Client Secret",
                    "required": True,
                },
                {
                    "label": "Client Cloud",
                    "name": "client_cloud",
                    "type": "select",
                    "options": [
                        {"label": "US-1", "value": "us-1"},
                        {"label": "US-2", "value": "us-2"},
                        {"label": "EU-1", "value": "eu-1"},
                        {"label": "US-GOV-1", "value": "us-gov-1"},
                    ],
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return CrowdstrikeIdentityProtectionIntegration

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
        token = _get_token(
            client_id=self.integration.client_id,
            client_secret=self.integration.client_secret,
            client_cloud=self.integration.client_cloud,
        )
        return RestAPICreds(
            base_url=_get_base_url(self.integration.client_cloud),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            envs={
                "FALCON_CLIENT_ID": self.integration.client_id,
                "FALCON_CLIENT_SECRET": self.integration.client_secret,
                "FALCON_CLOUD": self.integration.client_cloud,
            }
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        falconpy = importlib.import_module("falconpy", package=None)
        IdentityProtection = getattr(falconpy, "IdentityProtection")

        client = IdentityProtection(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )

        return [
            {
                "clients": {"identity_protection": client},
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
