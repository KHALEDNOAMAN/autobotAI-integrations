import importlib
import smtplib
from typing import List, Optional, Union

from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    CLICreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)

from autobotAI_integrations.models import IntegrationCategory
import imaplib


class IMAPIntegration(BaseSchema):
    host: Optional[str] = None
    port: Optional[str] = Field(default="993")
    smtp_host: Optional[str] = None
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = "IMAP is a protocol for email access and management."


class IMAPService(BaseService):

    def __init__(self, ctx: dict, integration: Union[IMAPIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, IMAPIntegration):
            integration = IMAPIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False):
        try:
            connection = imaplib.IMAP4_SSL(self.integration.host, self.integration.port)
            connection.login(self.integration.username, self.integration.password)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Email",
            "type": "form",
            "children": [
                {
                    "name": "host",
                    "type": "text",
                    "label": "IMAP Host",
                    "required": True,
                    "placeholder": "imap.example.com",
                },
                {
                    "name": "port",
                    "type": "text",
                    "label": "IMAP Port",
                    "placeholder": "default: 993",
                    "description": "- Port to connect on the host, usually 143 for IMAP and 993 for IMAPS. Valid values are 143, 993, or a value between 1024 and 65535. Default 993. ",
                    "required": False,
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Username",
                    "placeholder": "user@example.com",
                    "required": True,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "Password",
                    "required": True,
                },
                {
                    "name": "smtp_host",
                    "type": "text",
                    "label": "SMTP Host",
                    "description": "SMTP (SSL) Host to connect to. This is optional and required only if you wish to use smtp client",
                    "placeholder": "smtp.example.com",
                    "required": False,
                },
            ],
        }

    @staticmethod
    def get_schema():
        return IMAPIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        clients = {}
        connection = imaplib.IMAP4_SSL(
            payload_task.creds.envs["IMAP_HOST"], payload_task.creds.envs["IMAP_PORT"]
        )
        connection.login(
            payload_task.creds.envs["IMAP_USERNAME"], payload_task.creds.envs["IMAP_PASSWORD"]
        )
        clients["imap_ssl_connection"] = connection

        is_smtp_client = any(client.name == "smtp_client" for client in client_definitions)
        if is_smtp_client:
            smtp_host = (
                payload_task.creds.envs.get("SMTP_HOST")
                if payload_task.creds.envs.get("SMTP_HOST")
                else payload_task.creds.envs["IMAP_HOST"].replace("imap", "smtp")
            )
            smtp_client = smtplib.SMTP_SSL(smtp_host, 465)
            smtp_client.login(
                payload_task.creds.envs["IMAP_USERNAME"], payload_task.creds.envs["IMAP_PASSWORD"]
            )
            clients["smtp_client"] = smtp_client
        return [
            {
                "clients": clients,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "IMAP_HOST": self.integration.host,
            "IMAP_PORT": self.integration.port,
            "IMAP_LOGIN": self.integration.username,
            "IMAP_PASSWORD": self.integration.password,
        }
        conf_path = "~/.steampipe/config/imap.spc"
        config = """connection "imap" {
  plugin   = "imap"
}"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="imap",
            connection_name="imap",
            conf_path=conf_path,
            config=config,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "IMAP_HOST": self.integration.host,
            "IMAP_PORT": self.integration.port,
            "IMAP_USERNAME": self.integration.username,
            "IMAP_PASSWORD": self.integration.password,
        }
        if self.integration.smtp_host:
            envs["SMTP_HOST"] = self.integration.smtp_host
        return SDKCreds(envs=envs)
