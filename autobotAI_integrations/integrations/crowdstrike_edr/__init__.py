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


class CrowdstrikeEDRIntegration(BaseSchema):
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)
    client_cloud: Optional[str] = Field(default="us-2", exclude=True)

    name: Optional[str] = "CrowdStrike Endpoint Detection and Response"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CrowdStrike Falcon Endpoint Detection and Response (EDR) helps security "
        "teams detect, investigate, and respond to endpoint threats using real-time "
        "telemetry and threat intelligence."
    )


class CrowdstrikeEDRService(BaseService):
    def __init__(self, ctx: dict, integration: Union[CrowdstrikeEDRIntegration, dict]):
        if not isinstance(integration, CrowdstrikeEDRIntegration):
            integration = CrowdstrikeEDRIntegration(**integration)
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
                f"{base_url}/detects/queries/detects/v1",
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
                    f"EDR API check failed ({response.status_code}): "
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
            "label": "CrowdStrike EDR",
            "type": "form",
            "children": [
                {
                    "name": "client_id",
                    "type": "text",
                    "label": "Client ID",
                    "placeholder": "Enter the Falcon API Client ID",
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
        return CrowdstrikeEDRIntegration

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
        detects_client = getattr(falconpy, "Detects")(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )
        hosts_client = getattr(falconpy, "Hosts")(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )
        incidents_client = getattr(falconpy, "Incidents")(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )
        alerts_client = getattr(falconpy, "Alerts")(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )
        rtr_client = getattr(falconpy, "RealTimeResponse")(
            client_id=payload_task.creds.envs.get("FALCON_CLIENT_ID"),
            client_secret=payload_task.creds.envs.get("FALCON_CLIENT_SECRET"),
            base_url=payload_task.creds.envs.get("FALCON_CLOUD"),
        )

        return [
            {
                "clients": {
                    "detects": detects_client,
                    "hosts": hosts_client,
                    "incidents": incidents_client,
                    "alerts": alerts_client,
                    "real_time_response": rtr_client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]
