import importlib
import re
from typing import List, Optional, Type, Union
from zscaler import ZscalerClient
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

ONEAPI_BASE_URL = "https://api.zsapi.net"



def _get_token(client_id: str, client_secret: str, vanity_domain: str, cloud: Optional[str] = None) -> str:
    """
    Authenticate to Zscaler OneAPI using the OAuth2 client_credentials grant.
    Returns a Bearer access token on success or raises on failure.
    """
    config = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "vanityDomain": vanity_domain.strip(),
        "cloud": "" if not cloud else cloud,  # your ZIA cloud
    }
    client = ZscalerClient(config)
    client.authenticate()
    access_token = client._auth_token
    if not access_token:
        raise ValueError("Token response did not contain an access_token")
    return access_token


class ZscalerIntegration(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    vanity_domain: Optional[str] = Field(default=None, exclude=False)
    cloud: Optional[str] = Field(default=None, exclude=False)

    name: Optional[str] = "Zscaler"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Zscaler is a cloud-native zero trust platform providing secure internet and SaaS access, "
        "advanced threat protection, data loss prevention, and zero trust connectivity "
        "for users, workloads, and devices across ZIA, ZPA, ZDX, and more."
    )


class ZscalerService(BaseService):
    def __init__(self, ctx: dict, integration: Union[ZscalerIntegration, dict]):
        """
        Integration should have all the data regarding the integration.
        """
        if not isinstance(integration, ZscalerIntegration):
            integration = ZscalerIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            config = {
                "clientId": self.integration.client_id,
                "clientSecret": self.integration.client_secret,
                "vanityDomain": self.integration.vanity_domain.strip(),
                "cloud": "" if not self.integration.cloud else self.integration.cloud,  # your ZIA cloud
            }

            client = ZscalerClient(config)
            client.authenticate()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Zscaler",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text/password",
                    "label": "Client ID",
                    "placeholder": "Enter your Zscaler API Client ID",
                    "description": "API Client ID from ZIdentity (Administration > API Clients)",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter your Zscaler API Client Secret",
                    "required": True,
                },
                {
                    "name": "vanity_domain",
                    "type": "text",
                    "label": "Vanity Domain",
                    "placeholder": "e.g. mycompany",
                    "description": "Your organization's vanity domain (the part before .zslogin.net)",
                    "required": True,
                },
                {
                    "name": "cloud",
                    "type": "text",
                    "label": "Cloud",
                    "placeholder": "Leave Empty if .zslogin.net",
                    "description": "Your organization's custom cloud parameter, i.e. mycompany.zslogin{cloud}.net",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return ZscalerIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_rest_api_creds(self) -> RestAPICreds:
        """
        Authenticates via OneAPI client_credentials and returns REST API
        credentials with the Bearer token injected into the headers.
        """
        token = _get_token(
            client_id=self.integration.client_id,
            client_secret=self.integration.client_secret,
            vanity_domain=self.integration.vanity_domain,
            cloud=self.integration.cloud,
        )
        return RestAPICreds(
            base_url=f"{ONEAPI_BASE_URL}/zia",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "ZSCALER_CLIENT_ID": self.integration.client_id,
            "ZSCALER_CLIENT_SECRET": self.integration.client_secret,
            "ZSCALER_VANITY_DOMAIN": self.integration.vanity_domain,
            "ZSCALER_CLOUD": "" if not self.integration.cloud else self.integration.cloud,
        }
        return SDKCreds(envs=envs)

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        zscaler_module = importlib.import_module("zscaler", package=None)
        ZscalerClient = getattr(zscaler_module, "ZscalerClient")

        config = {
            "clientId": payload_task.creds.envs.get("ZSCALER_CLIENT_ID"),
            "clientSecret": payload_task.creds.envs.get("ZSCALER_CLIENT_SECRET"),
            "vanityDomain": payload_task.creds.envs.get("ZSCALER_VANITY_DOMAIN"),
            "cloud": payload_task.creds.envs.get("ZSCALER_CLOUD"),
        }

        client = ZscalerClient(config)
        client.__enter__()

        return [
            {
                "clients": {
                    "zscaler": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
