"""Bi-directional Microsoft Teams bot integration.

Unlike the outbound-only ``ms_teams`` Incoming Webhook integration,
``ms_teams_bot`` registers an Azure Bot / Teams app so users can talk to
Optimus and Optimus can post back. REST-only (Bot Framework Connector).

Secrets (``app_password``) use ``Field(exclude=True)`` so the crypto layer
encrypts them at rest. ``app_id`` / ``tenant_id`` are plaintext metadata
(also used as JWT audience on the ListenerV2 secret).
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


class MsTeamsBotIntegration(BaseSchema):
    app_password: Optional[str] = Field(default=None, exclude=True)

    app_id: Optional[str] = None
    tenant_id: Optional[str] = None
    bot_id: Optional[str] = None
    listener_id: Optional[str] = None
    webhook_url: Optional[str] = None
    # {aad_object_id_or_upn: autobotai_user_email}
    user_overrides: Optional[Dict[str, str]] = None

    category: Optional[str] = IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    description: Optional[str] = (
        "Bi-directional Microsoft Teams bot: talk to Optimus from Teams and "
        "let Optimus post back. Default surface is a per-user private Team "
        "channel (reply chains). Grant Graph application permissions "
        "User.Read.All (or User.ReadBasic.All), Team.ReadBasic.All, "
        "Group.Create, Team.Create, "
        "Channel.ReadBasic.All, AppCatalog.Read.All, and "
        "TeamsAppInstallation.ReadWriteSelfForTeam.All with admin consent; "
        "publish the app to the org catalog. Personal DM is fallback only."
    )


class MsTeamsBotService(BaseService):
    def __init__(self, ctx, integration: MsTeamsBotIntegration):
        if not isinstance(integration, MsTeamsBotIntegration):
            integration = MsTeamsBotIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        """Acquire a Bot Framework client-credentials token (single-tenant)."""
        try:
            app_id = self.integration.app_id
            app_password = self.integration.app_password
            tenant_id = self.integration.tenant_id
            if not (app_id and app_password and tenant_id):
                return {
                    "success": False,
                    "error": "app_id, app_password, and tenant_id are required",
                }
            token_url = (
                f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            )
            resp = requests.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": app_id,
                    "client_secret": app_password,
                    "scope": "https://api.botframework.com/.default",
                },
                timeout=15,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400 or not data.get("access_token"):
                return {
                    "success": False,
                    "error": data.get("error_description")
                    or data.get("error")
                    or f"token request failed ({resp.status_code})",
                }
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
        return MsTeamsBotIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    @staticmethod
    def get_forms():
        return {
            "label": "Microsoft Teams Bot (bi-directional)",
            "type": "form",
            "children": [
                {
                    "label": "Microsoft Teams Bot",
                    "type": "form",
                    "formId": "ms_teams_bot_integration",
                    "children": [
                        {
                            "name": "app_id",
                            "type": "text",
                            "label": "Microsoft App ID",
                            "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                            "required": True,
                            "description": (
                                "Entra Application (client) ID. On this app, add "
                                "Microsoft Graph application permissions "
                                "User.Read.All (or User.ReadBasic.All), "
                                "Team.ReadBasic.All, Group.Create, "
                                "Team.Create, Channel.ReadBasic.All, AppCatalog.Read.All, and "
                                "TeamsAppInstallation.ReadWriteSelfForTeam.All, "
                                "then Grant admin consent. Required for email → Entra "
                                "lookup and per-user private Optimus Team channels."
                            ),
                            "help_url": (
                                "https://learn.microsoft.com/en-us/graph/"
                                "permissions-reference#user-permissions"
                            ),
                            "help_url_text": "Graph user permissions ↗",
                        },
                        {
                            "name": "app_password",
                            "type": "password",
                            "label": "Microsoft App Password / Client Secret",
                            "required": True,
                        },
                        {
                            "name": "tenant_id",
                            "type": "text",
                            "label": "Entra Tenant ID",
                            "description": (
                                "Azure AD tenant where the single-tenant bot "
                                "app is registered (not Optimus root_user_id). "
                                "Also use Teams admin center → Manage apps to "
                                "publish the Optimus ZIP and Edit installs → "
                                "Everyone (personal scope) for org-wide DMs."
                            ),
                            "required": True,
                        },
                        {
                            "name": "webhook_url",
                            "type": "text",
                            "label": "Messaging endpoint",
                            "description": (
                                "Paste this into Azure Bot → Configuration → "
                                "Messaging endpoint. Populated after save."
                            ),
                            "readOnly": True,
                        },
                    ],
                }
            ],
        }

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url="https://smba.trafficmanager.net/teams/",
            token=None,
            headers={},
            envs={
                "TEAMS_BOT_APP_ID": self.integration.app_id,
                "TEAMS_BOT_APP_PASSWORD": self.integration.app_password,
                "TEAMS_BOT_TENANT_ID": self.integration.tenant_id,
            },
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(
            envs={
                "TEAMS_BOT_APP_ID": self.integration.app_id,
                "TEAMS_BOT_APP_PASSWORD": self.integration.app_password,
                "TEAMS_BOT_TENANT_ID": self.integration.tenant_id,
            }
        )
