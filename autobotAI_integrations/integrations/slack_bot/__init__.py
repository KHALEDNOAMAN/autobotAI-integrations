"""Bi-directional Slack bot integration.

Unlike the outbound-only ``slack`` integration, ``slack_bot`` registers a
per-deployment Slack App (events + interactivity) so a Slack user can talk to
Optimus and Optimus can post back. REST-only — no slack-sdk dependency
(4 endpoints: auth.test, users.info, chat.postMessage, chat.update).

Secrets (``bot_token``, ``signing_secret``) use ``Field(exclude=True)`` so the
crypto layer encrypts them at rest, exactly like ``slack.bot_token``. The
plaintext metadata fields (app_id/team_id/…) are normal fields.
"""

from typing import Dict, List, Optional

import requests
from pydantic import Field

from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
    RestAPICreds,
    SDKCreds,
)
from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils.logging_config import logger

_SLACK_API = "https://slack.com/api"


class SlackBotIntegration(BaseSchema):
    # Secrets — encrypted at rest (exclude=True), never returned to the FE.
    bot_token: Optional[str] = Field(default=None, exclude=True)
    signing_secret: Optional[str] = Field(default=None, exclude=True)

    # Populated by _test_integration via auth.test (plaintext metadata).
    app_id: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    bot_user_id: Optional[str] = None
    # Set by core when the backing ListenerV2 is minted on save.
    listener_id: Optional[str] = None
    # Display-only: the per-deployment events/interactivity request URL.
    webhook_url: Optional[str] = None
    # {slack_user_id: autobotai_user_email} for SSO email-mismatch / guests.
    user_overrides: Optional[Dict[str, str]] = None

    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "Bi-directional Slack bot: talk to Optimus from Slack and let Optimus "
        "post back, with interactive approval buttons (HITL)."
    )


class SlackBotService(BaseService):
    def __init__(self, ctx, integration: SlackBotIntegration):
        if not isinstance(integration, SlackBotIntegration):
            integration = SlackBotIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        """REST auth.test (no slack-sdk). On success, hydrate app/team/bot ids."""
        try:
            resp = requests.post(
                f"{_SLACK_API}/auth.test",
                headers={"Authorization": f"Bearer {self.integration.bot_token}"},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                return {"success": False, "error": data.get("error", "auth.test failed")}
            # Hydrate metadata for re-display.
            self.integration.team_id = data.get("team_id")
            self.integration.team_name = data.get("team")
            self.integration.bot_user_id = data.get("user_id")
            self.integration.app_id = data.get("app_id") or self.integration.app_id
            return {"success": True}
        except Exception as e:
            logger.error(e)
            return {"success": False, "error": str(e)}

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "lambda",
            "supported_interfaces": cls.supported_connection_interfaces(),
        }

    @staticmethod
    def get_schema(ctx=None):
        return SlackBotIntegration

    @staticmethod
    def supported_connection_interfaces():
        # REST-only; agent slack tools read SLACK_BOT_TOKEN from injected env.
        return [ConnectionInterfaces.REST_API]

    @staticmethod
    def get_forms():
        return {
            "label": "Slack Bot (bi-directional)",
            "type": "form",
            "children": [
                {
                    "label": "Slack Bot",
                    "type": "form",
                    "formId": "slack_bot_integration",
                    "children": [
                        {
                            "name": "bot_token",
                            "type": "password",
                            "label": "Bot User OAuth Token",
                            "placeholder": "xoxb-...",
                            "required": True,
                        },
                        {
                            "name": "signing_secret",
                            "type": "password",
                            "label": "Signing Secret",
                            "placeholder": "Slack app signing secret",
                            "description": "Used to verify event + interactivity requests.",
                            "required": True,
                        },
                        {
                            "name": "webhook_url",
                            "type": "text",
                            "label": "Request URL (events + interactivity)",
                            "description": "Paste this into your Slack App config. "
                            "Populated after the first save.",
                            "readOnly": True,
                        },
                    ],
                }
            ],
        }

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=_SLACK_API,
            token=self.integration.bot_token,
            headers={"Authorization": f"Bearer {self.integration.bot_token}"},
            envs={
                "SLACK_BOT_TOKEN": self.integration.bot_token,
                "SLACK_SIGNING_SECRET": self.integration.signing_secret,
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        # Provided so the agent's slack tools always get SLACK_BOT_TOKEN in env,
        # regardless of which cred path _build_tasks uses. No slack-sdk import.
        return SDKCreds(envs={"SLACK_BOT_TOKEN": self.integration.bot_token})
