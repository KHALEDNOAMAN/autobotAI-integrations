from enum import Enum
from typing import List, Optional

from pydantic import Field
import requests

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    RestAPICreds,
    SDKCreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)
from slack_sdk import WebClient
from slack_sdk.webhook import WebhookClient

from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils import list_of_unique_elements
from autobotAI_integrations.utils.logging_config import logger

class SlackAuthTypes(str, Enum):
    WEBHOOK_INTEGRATION = "webhook_integration"
    TOKEN_INTEGRATION = "token_integration"

class SlackIntegration(BaseSchema):
    webhook: Optional[str] = None
    workspace: Optional[str] = None
    bot_token: Optional[str] = Field(default=None, exclude=True)

    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "A popular collaboration platform for teams, known for its ease of use, integrations with various services, and focus on real-time communication."
    )


class SlackService(BaseService):
    def __init__(self, ctx, integration: SlackIntegration):
        if not isinstance(integration, SlackIntegration):
            integration = SlackIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            if self.integration.webhook not in [None, "None"]:
                response = requests.post(self.integration.webhook)
                if response.status_code == 400 and response.text == "invalid_payload":
                    return {"success": True}
                else:
                    return {"success": False, "error": response.text}
            else:
                client = WebClient(token=self.integration.bot_token)
                response = client.conversations_list()
            return {"success": True}
        except Exception as e:
            logger.error(e)
            return {"success": False, "error": str(e)}

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "lambda",
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def get_integration_specific_details(self):
        try:
            details = {}
            details["integration_id"] = self.integration.accountId
            if self.integration.webhook in [None, "None"]:
                client = WebClient(token=self.integration.bot_token)
                channels = self._get_all_channels_name(client)
                if channels:
                    details["channels"] = channels
            return details
        except Exception as e:
            logger.error(e)
            return {"error": "Details can not be fetched"}

    @staticmethod
    def get_forms():
        return {
            "label": "Slack",
            "type": "form",
            "children": [
                {
                    "label": "Webhook Integration",
                    "type": "form",
                    "formId": SlackAuthTypes.WEBHOOK_INTEGRATION.value,
                    "children": [
                        {
                            "name": "webhook",
                            "type": "text/url",
                            "label": "Webhook URL",
                            "placeholder": "Enter your Webhook URL",
                            "required": True,
                        }
                    ],
                },
                {
                    "label": "Bot Token Integration",
                    "type": "form",
                    "formId": SlackAuthTypes.TOKEN_INTEGRATION.value,
                    "children": [
                        {
                            "name": "workspace",
                            "type": "text",
                            "label": "Workspace Name",
                            "placeholder": "Enter the Slack Workspace Name",
                            "description": "the name of workspace in which the bot is installed in",
                        },
                        {
                            "name": "bot_token",
                            "type": "text",
                            "label": "Slack Bot Token",
                            "placeholder": "Enter the Slack Token",
                            "description": "Scopes needed: channels:read, groups:read, im:read, mpin:read",
                            "required": True,
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def get_schema():
        return SlackIntegration

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
        if payload_task.creds.envs.get("SLACK_WEBHOOK"):
            webhook = WebhookClient(payload_task.creds.envs.get("SLACK_WEBHOOK"))
            clients["WebhookClient"] = webhook
        else:
            clients["WebClient"] = WebClient(
                payload_task.creds.envs.get("SLACK_BOT_TOKEN")
            )

        return [
            {
                "clients": clients,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "SLACK_TOKEN": self.integration.bot_token,
        }
        conf_path = "~/.steampipe/config/slack.spc"
        config_str = """connection "slack" {
  plugin = "slack"
}
"""
        return SteampipeCreds(
            envs=envs,
            plugin_name="slack",
            connection_name="slack",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {}
        if self.integration.webhook not in [None, "None"]:
            envs["SLACK_WEBHOOK"] = self.integration.webhook
        if self.integration.bot_token not in [None, "None"]:
            envs["SLACK_BOT_TOKEN"] = self.integration.bot_token
        return SDKCreds(envs=envs)

    @staticmethod
    def _get_all_channels_name(client, iteration_count=10):
        channels, count = [], 0
        try:
            # Initialize pagination
            next_cursor = None
            while count < iteration_count:
                # Call the conversations.list API
                response = client.conversations_list(
                    exclude_archived=True,
                    limit=1000,
                    types="public_channel, private_channel",
                    cursor=next_cursor,  # Cursor for pagination
                )

                # Add the channels from the current response
                channels.extend(
                    [channel.get("name") for channel in response.get("channels")]
                )

                # Check for the next cursor
                next_cursor = response.get("response_metadata", {}).get("next_cursor")
                count += 1
                if not next_cursor:
                    break  # Exit the loop if there's no next page

        except Exception as e:
            print(f"Error fetching channels: {e}")

        return channels
