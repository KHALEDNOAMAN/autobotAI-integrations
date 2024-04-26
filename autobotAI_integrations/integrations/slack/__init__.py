import importlib
import uuid
from typing import List, Optional

from pydantic import Field

from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from slack_sdk import WebClient

class SlackIntegration(BaseSchema):
    workspace: Optional[str] = None
    bot_token: str = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class SlackService(BaseService):

    def __init__(self, ctx, integration: SlackIntegration):
        super().__init__(ctx, integration)
    
    def _test_integration(self):
        try:
            client = WebClient(token=self.integration.bot_token)
            client.usergroups_list()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Slack",
            "type": "form",
            "children": [
                {
                    "label": "Bot Token Integration",
                    "type": "form",
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
                            "required": True
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def get_schema():
        return SlackIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE
        ]

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        slack = importlib.import_module(client_definitions[0].import_library_names[0], package=None)

        return [
            {
                "clients": {
                    "WebClient": slack.WebClient(token=self.integration.bot_token)
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
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
        return SteampipeCreds(envs=envs, plugin_name="slack", connection_name="slack",
                              conf_path=conf_path, config=config_str)

    def generate_rest_api_creds(self) -> RestAPICreds:
        pass

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "SLACK_BOT_TOKEN": self.integration.bot_token,
        }
        return SDKCreds(envs=envs)
