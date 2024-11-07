from typing import List, Type, Union

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


class GrafanaIntegrations(BaseSchema):
    host_url: Optional[str] = Field(default=None, exclude=True)
    auth_key: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Grafana is a cloud hosting company that provides virtual private servers and other infrastructure services."
    )


class GrafanaService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GrafanaIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GrafanaIntegrations):
            integration = GrafanaIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            if len(self.integration.auth_key.split(":")) > 1:
                response = requests.get(f"https://{self.integration.auth_key}@{self.integration.host_url.split('://')[1]}/api/user")
            else:
                response = requests.get(
                    f"{self.integration.host_url}/api/user",
                    headers={"Authorization": f"Bearer {self.integration.auth_key}"},
                )
            if response.status_code == 200:
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is unreachable"}

    @staticmethod
    def get_forms():
        return {
            "label": "Grafana",
            "type": "form",
            "children": [
                {
                    "name": "host_url",
                    "label": "Host URL",
                    "type": "text",
                    "placeholder": "grafana host url",
                    "required": True,
                },
                {
                    "name": "auth_key",
                    "label": "Auth Key",
                    "type": "text/password",
                    "placeholder": "Service account token or username:password",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GrafanaIntegrations

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = {
            "GRAFANA_URL": self.integration.host_url,
            "GRAFANA_AUTH": self.integration.auth_key,
        }
        conf_path = "~/.steampipe/config/grafana.spc"
        config = """connection "grafana" {
  plugin = "grafana"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="grafana",
            connection_name="grafana",
            conf_path=conf_path,
            config=config,
        )
