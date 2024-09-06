import importlib
from typing import List, Optional, Union

from pydantic import Field

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
import requests
import uuid


class SnowflakeIntegration(BaseSchema):
    account: str
    username: str
    password: Optional[str] = Field(default=None, exclude=True)
    account_locator: Optional[str] = None
    region: Optional[str] = None

    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "Snowflake enables data storage, processing, and analytic solutions that are faster, easier to use, and far more flexible than traditional offerings."
    )
    
    
    def __init__(self, **kwargs):
        if "accountId" not in kwargs:
            kwargs["accountId"] = f"{kwargs.get('account')}_{kwargs.get('username')}"
        super().__init__(**kwargs)


class SnowflakeService(BaseService):

    def __init__(self, ctx: dict, integration: Union[SnowflakeIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, SnowflakeIntegration):
            integration = SnowflakeIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self):
        try:
            response = requests.post(
                f"https://{self.integration.account}.snowflakecomputing.com/session/v1/login-request",
                headers={"Content-Type": "application/json"},
                json={
                    "data": {
                        "ACCOUNT": self.integration.account,
                        "LOGIN_NAME": self.integration.username,
                        "PASSWORD": self.integration.password,
                    }
                },
            )
            if response.status_code == 200:
                if response.json().get('success'):
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": "Incorrect username or password",
                    }
            else:
                return {
                    "success": False,
                    "error": f"Request failed with status code: {response.status_code}",
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Snowflake",
            "type": "form",
            "children": [
                {
                    "name": "account",
                    "type": "text",
                    "label": "Account",
                    "required": True,
                    "placeholder": "ex: xy123",
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Username",
                    "required": True,
                    "placeholder": "my_username123",
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "Password",
                    "required": True,
                    "placeholder": "password",
                },
                # {
                #     "name": "account_locator",
                #     "type": "text",
                #     "label": "Account Locator",
                #     "required": True,
                #     "placeholder": "Account Locator",
                # },
                # {
                #     "name": "region",
                #     "type": "text",
                #     "label": "Region",
                #     "required": True,
                #     "placeholder": "example: ap-southeast-1",
                # },
            ],
        }

    @staticmethod
    def get_schema():
        return SnowflakeIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            # ConnectionInterfaces.STEAMPIPE,
            # ConnectionInterfaces.REST_API
        ]

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        connector = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        return [
            {
                "clients": {
                    "snowflake": connector.connect(
                        user=payload_task.creds.envs.get("SNOWFLAKE_USERNAME"),
                        password=payload_task.creds.envs.get("SNOWFLAKE_PASSWORD"),
                        account=payload_task.creds.envs.get("SNOWFLAKE_ACCOUNT"),
                    )
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        conf_path = "~/.steampipe/config/snowflake.spc"
        config_str = f"""connection "snowflake" {{
  plugin = "snowflake"
  account = "{self.integration.account_locator}"
  user = "{self.integration.username}"
  password = "{self.integration.password}"
  region = "{self.integration.region}"
}}
"""
        return SteampipeCreds(
            envs={},
            plugin_name="snowflake",
            connection_name="snowflake",
            conf_path=conf_path,
            config=config_str,
        )

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "SNOWFLAKE_ACCOUNT": self.integration.account,
            "SNOWFLAKE_USERNAME": self.integration.username,
            "SNOWFLAKE_PASSWORD": self.integration.password,
        }
        return SDKCreds(envs=envs)
