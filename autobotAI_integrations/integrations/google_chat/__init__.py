from typing import Type, Union

import uuid
import re

from autobotAI_integrations import BaseService, PayloadTask
from .webhook_client import GoogleChatWebhookClient
from autobotAI_integrations.models import *


class GoogleChatIntegration(BaseSchema):
    webhook: str
    account_id: Optional[str] = None

    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "Google Chat integrates with various apps and services to enhance communication and collaboration."
    )


class GoogleChatService(BaseService):
    # TODO: This Service Can be Much More Better by Adding actual google.cloud.apis
    # More details: https://developers.google.com/workspace/chat/overview
    def __init__(self, ctx: dict, integration: Union[GoogleChatIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GoogleChatIntegration):
            integration = GoogleChatIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        pattern = re.compile(
            "https://chat.googleapis.com/v1/spaces/[a-zA-Z0-9].*?/messages?.*"
        )
        result = pattern.match(self.integration.webhook)
        res = None
        if result is None:
            res = {
                "success": False,
                "error": "Webhook is not valid Google Chat webhook URL",
            }
        try:
            if not res:
                client = GoogleChatWebhookClient(
                    url=self.integration.webhook, header="autobotAI"
                )
                client.send("Hello from autobotAI!!!", "The webhook works!!!")
                res = {"success": True}
        except:
            res = {
                "success": False,
                "error": "Unable to send message to Google Chat webhook",
            }

        return res

    @staticmethod
    def get_forms():
        return {
            "label": "Google Chat",
            "type": "form",
            "children": [
                {
                    "label": "Channel Webhook Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "webhook",
                            "type": "text/url",
                            "label": "Webhook URL",
                            "placeholder": "Enter your Webhook URL",
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GoogleChatIntegration

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask, client_definitions: List[SDKClient]) -> list:
        return [
            {
                "clients": {
                    "google_chat_webhook": GoogleChatWebhookClient(
                        url=self.integration.webhook, header="autobotAI"
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        return SDKCreds(envs={})

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API,
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()
