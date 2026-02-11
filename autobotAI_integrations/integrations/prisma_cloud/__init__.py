from typing import Optional, Type, Union
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests
from pydantic import Field

from autobotAI_integrations.models import IntegrationCategory, SteampipeCreds


class PrismaCloudIntegrations(BaseSchema):
    url: Optional[str] = Field(default=None, exclude=True)
    access_key_id: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Prisma Cloud"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Prisma Cloud by Palo Alto Networks is a comprehensive Cloud Native Application Protection Platform (CNAPP) "
        "that provides Cloud Security Posture Management (CSPM), Cloud Workload Protection (CWP), Cloud Infrastructure "
        "Entitlement Management (CIEM), and Cloud Network Security (CNS) capabilities across multi-cloud environments."
    )


class PrismaCloudService(BaseService):

    def __init__(self, ctx: dict, integration: Union[PrismaCloudIntegrations, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, PrismaCloudIntegrations):
            integration = PrismaCloudIntegrations(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            # Test Prisma Cloud API connectivity
            # Authenticate and get token
            auth_url = f"{self.integration.url}/login"
            auth_payload = {
                "username": self.integration.access_key_id,
                "password": self.integration.secret_key
            }
            
            # TODO: Uncomment when ready to test with actual API
            return {"success": True}
            
            # response = requests.post(auth_url, json=auth_payload, timeout=10)
            # if response.status_code == 200:
            #     return {"success": True}
            # else:
            #     return {
            #         "success": False,
            #         "error": f"Authentication failed. Status code: {response.status_code}",
            #     }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": "Connection is unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Prisma Cloud",
            "type": "form",
            "children": [
                {
                    "name": "url",
                    "type": "text",
                    "label": "Prisma Cloud API URL",
                    "placeholder": "Enter the Prisma Cloud API URL (e.g., https://api.prismacloud.io)",
                    "required": True,
                },
                {
                    "name": "access_key_id",
                    "type": "text",
                    "label": "Access Key ID",
                    "placeholder": "Enter the Prisma Cloud Access Key ID",
                    "required": True,
                },
                {
                    "name": "secret_key",
                    "type": "text/password",
                    "label": "Secret Key",
                    "placeholder": "Enter the Prisma Cloud Secret Key",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return PrismaCloudIntegrations

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "ecs",
            "compliance_supported": True,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "preview": True
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.CLI,
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        """
        Generate Steampipe credentials for Prisma Cloud
        Note: This is a placeholder as Prisma Cloud doesn't have an official Steampipe plugin yet
        """
        creds = {
            "PRISMA_CLOUD_URL": self.integration.url,
            "PRISMA_CLOUD_ACCESS_KEY": self.integration.access_key_id,
            "PRISMA_CLOUD_SECRET_KEY": self.integration.secret_key,
        }
        conf_path = "~/.steampipe/config/prisma_cloud.spc"
        config = """connection "prisma_cloud" {
  plugin = "prisma_cloud"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="prisma_cloud",
            connection_name="prisma_cloud",
            conf_path=conf_path,
            config=config,
        )
