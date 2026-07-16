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
from autobotAI_integrations.models import IntegrationCategory, SteampipeCreds

CLOUD_BASE_URLS = {
    "us-1": "https://api.crowdstrike.com",
    "us-2": "https://api.us-2.crowdstrike.com",
    "eu-1": "https://api.eu-1.crowdstrike.com",
    "us-gov-1": "https://api.laggar.gcw.crowdstrike.com",
}


def _get_base_url(client_cloud: str) -> str:
    """Return the Falcon API base URL for the given cloud region."""
    return CLOUD_BASE_URLS.get(client_cloud, CLOUD_BASE_URLS["us-2"])


def _get_token(client_id: str, client_secret: str, client_cloud: str) -> str:
    """Obtain a short-lived OAuth2 bearer token from the Falcon platform."""
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
    access_token = response.json().get("access_token")
    if not access_token:
        raise ValueError("Token response did not contain an access_token")
    return access_token


class CrowdstrikeIntegrations(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    client_cloud: Optional[str] = Field(default="us-2", exclude=True)

    name: Optional[str] = "CrowdStrike"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CrowdStrike provides cloud workload and endpoint security, threat intelligence, and cyberattack response services."
    )


class CrowdstrikeService(BaseService):

    def __init__(self, ctx: dict, integration: Union[CrowdstrikeIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, CrowdstrikeIntegrations):
            integration = CrowdstrikeIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # A successfully generated token confirms valid credentials.
            # The token works for all CrowdStrike API endpoints the API key's scopes allow —
            # no additional endpoint probing is needed.
            _get_token(
                client_id=self.integration.client_id,
                client_secret=self.integration.client_secret,
                client_cloud=self.integration.client_cloud,
            )
            return {"success": True}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is unreachable"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"Authentication failed: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Crowdstrike",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter the Client ID",
                    "required": True,
                    "help_url": "https://falcon.crowdstrike.com/support/api-clients-and-keys",
                    "help_url_text": "Get Client ID ↗",
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter the Client Secret",
                    "required": True,
                    "help_url": "https://falcon.crowdstrike.com/support/api-clients-and-keys",
                    "help_url_text": "Get Client Secret ↗",
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
        return CrowdstrikeIntegrations

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "preview": True
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {
            "FALCON_CLIENT_ID": self.integration.client_id,
            "FALCON_CLIENT_SECRET": self.integration.client_secret,
            "FALCON_CLOUD": self.integration.client_cloud,
        }
        conf_path = "~/.steampipe/config/crowdstrike.spc"
        config = """connection "crowdstrike" {
  plugin = "crowdstrike"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="crowdstrike",
            connection_name="crowdstrike",
            conf_path=conf_path,
            config=config,
        )

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
        client_id = payload_task.creds.envs.get("FALCON_CLIENT_ID")
        client_secret = payload_task.creds.envs.get("FALCON_CLIENT_SECRET")
        client_cloud = payload_task.creds.envs.get("FALCON_CLOUD")

        def _make_client(class_name: str):
            return getattr(falconpy, class_name)(
                client_id=client_id,
                client_secret=client_secret,
                base_url=client_cloud,
            )

        return [
            {
                "clients": {
                    "detects": _make_client("Detects"),
                    "hosts": _make_client("Hosts"),
                    "incidents": _make_client("Incidents"),
                    "alerts": _make_client("Alerts"),
                    "real_time_response": _make_client("RealTimeResponse"),
                    "identity_protection": _make_client("IdentityProtection"),
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
