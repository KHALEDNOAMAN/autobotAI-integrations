import base64
from enum import Enum
import importlib
from typing import List, Optional

from pydantic import Field, field_validator
import requests

from autobotAI_integrations import (
    BaseSchema,
    SteampipeCreds,
    SDKCreds,
    BaseService,
    ConnectionInterfaces,
    PayloadTask,
    SDKClient,
)

from autobotAI_integrations.models import IntegrationCategory
from autobotAI_integrations.utils.logging_config import logger


class DatabricksAuthTypes(str, Enum):
    WORKSPACE = "workspace"
    ACCOUNT_AND_WORKSPACE = "account_and_workspace"


class DatabricksIntegration(BaseSchema):
    account_id: Optional[str] = Field(default=None, exclude=True)
    account_host: Optional[str] = Field(
        default="https://accounts.cloud.databricks.com/"
    )

    # For workspace
    workspace_host: Optional[str] = Field(default=None, exclude=True)
    client_id: Optional[str] = Field(default=None, exclude=True)
    client_secret: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Databricks"
    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Databricks is a unified set of tools for building, deploying, sharing, and maintaining enterprise-grade data solutions at scale."
    )

    @field_validator("account_host", mode="before")
    @classmethod
    def validate_account_host(cls, account_host):
        if account_host.strip() == "":
            return "https://accounts.cloud.databricks.com/"
        return account_host

    def __init__(self, *args, **kwargs):
        if not kwargs.get("accountId"):
            if not kwargs.get('account_id'):
                kwargs["account_id"] = kwargs.get("client_id")
            kwargs["accountId"] = kwargs["account_id"]
        return super().__init__(*args, **kwargs)


class DatabricksService(BaseService):
    def __init__(self, ctx, integration: DatabricksIntegration):
        if not isinstance(integration, DatabricksIntegration):
            integration = DatabricksIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            url = f"{self.integration.workspace_host}/oidc/v1/token"
            data = {"grant_type": "client_credentials", "scope": "all-apis"}

            response = requests.post(
                url,
                headers={
                    "Authorization": f"Basic {base64.b64encode('{}:{}'.format(self.integration.client_id, self.integration.client_secret).encode()).decode()}"
                },
                data=data,
            )
            response.raise_for_status()
            return {"success": True}
        except Exception as e:
            logger.error(e)
            return {"success": False, "error": str(e)}

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def get_forms():
        return {
            "label": "Databricks",
            "type": "form",
            "children": [
                {
                    "name": "account_id",
                    "type": "text",
                    "label": "Account ID",
                    "placeholder": "Enter the Account ID",
                    "required": False,
                },
                {
                    "name": "account_host",
                    "type": "text",
                    "label": "Account Host",
                    "placeholder": "default: https://accounts.cloud.databricks.com/",
                    "required": False,
                },
                {
                    "name": "workspace_host",
                    "type": "text",
                    "label": "Workspace Host",
                    "placeholder": "Enter the Workspace Host",
                    "required": True,
                },
                {
                    "name": "client_id",
                    "type": "text/password",
                    "label": "Client Id",
                    "placeholder": "Enter the Client Id",
                    "required": True,
                },
                {
                    "name": "client_secret",
                    "type": "text/password",
                    "label": "Client Secret",
                    "placeholder": "Enter the Client Secret",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None):
        return DatabricksIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.STEAMPIPE,
        ]

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        clients_classes = dict()
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.import_library_names[0], package=None)
                if hasattr(client_module, client.name):
                    cls = getattr(client_module, client.name)
                    if client.name == "AccountClient":
                        clients_classes[client.name] = cls(
                            host=payload_task.creds.envs["DATABRICKS_ACCOUNT_HOST"],
                            account_id=payload_task.creds.envs["DATABRICKS_ACCOUNT_ID"],
                            client_id=payload_task.creds.envs["DATABRICKS_CLIENT_ID"],
                            client_secret=payload_task.creds.envs[
                                "DATABRICKS_CLIENT_SECRET"
                            ],
                        )
                    elif client.name == "WorkspaceClient":
                        clients_classes[client.name] = cls(
                            host=payload_task.creds.envs["DATABRICKS_HOST"],
                            account_id=payload_task.creds.envs["DATABRICKS_ACCOUNT_ID"],
                            client_id=payload_task.creds.envs["DATABRICKS_CLIENT_ID"],
                            client_secret=payload_task.creds.envs[
                                "DATABRICKS_CLIENT_SECRET"
                            ],
                        )
                    else: 
                        # Assuming the other clients takes workspace host
                        clients_classes[client.name] = cls(
                            host=payload_task.creds.envs["DATABRICKS_HOST"],
                            account_id=payload_task.creds.envs["DATABRICKS_ACCOUNT_ID"],
                            client_id=payload_task.creds.envs["DATABRICKS_CLIENT_ID"],
                            client_secret=payload_task.creds.envs[
                                "DATABRICKS_CLIENT_SECRET"
                            ],
                        )
            except Exception as e:
                logger.error(str(e))
                clients_classes[client.name] = None
        return [
            {
                "clients": clients_classes,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        conf_path = "~/.steampipe/config/databricks.spc"
        config_str = f"""connection "databricks" {{
  plugin = "databricks"
  account_host = "{self.integration.account_host}"
}}
"""
        return SteampipeCreds(
            envs=self._temp_credentials(),
            plugin_name="databricks",
            connection_name="databricks",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        return SDKCreds(envs=self._temp_credentials())

    def _temp_credentials(self):
        return {
            "DATABRICKS_ACCOUNT_HOST": self.integration.account_host,
            "DATABRICKS_HOST": self.integration.workspace_host,
            "DATABRICKS_ACCOUNT_ID": self.integration.account_id,
            "DATABRICKS_CLIENT_ID": self.integration.client_id,
            "DATABRICKS_CLIENT_SECRET": self.integration.client_secret,
        }
