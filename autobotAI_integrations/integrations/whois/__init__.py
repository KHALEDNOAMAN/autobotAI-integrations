from typing import List, Type, Union

from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests


class WhoisIntegrations(BaseSchema):
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "WHOIS is a widely used Internet record listing that identifies who owns a domain and how to get in contact with them"
    )


class WhoisService(BaseService):

    def __init__(self, ctx: dict, integration: Union[WhoisIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, WhoisIntegrations):
            integration = WhoisIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        return {"success": True}

    @staticmethod
    def get_forms():
        return {
            "label": "WHOIS",
            "type": "form",
            "children": [],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return WhoisIntegrations

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
        creds = {}
        conf_path = "~/.steampipe/config/whois.spc"
        config = """connection "whois" {
  plugin = "whois"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="whois",
            connection_name="whois",
            conf_path=conf_path,
            config=config,
        )
