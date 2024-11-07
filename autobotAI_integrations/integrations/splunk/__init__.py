import importlib
from typing import Type, Union
from autobotAI_integrations.models import *
from autobotAI_integrations import (
    BaseSchema,
    BaseService,
    ConnectionInterfaces,
)
import requests

from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils import list_of_unique_elements
import urllib.parse
import ssl
from xml.etree import ElementTree
import http.client
from autobotAI_integrations.utils.logging_config import logger


class SplunkIntegration(BaseSchema):
    username: Optional[str] = Field(default=None, exclude=True)
    password: Optional[str] = Field(default=None, exclude=True)

    host_url: Optional[str] = None

    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "Splunk software is used for searching, monitoring and analyzing log data."
    )


class SplunkService(BaseService):

    def __init__(self, ctx: dict, integration: Union[SplunkIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, SplunkIntegration):
            integration = SplunkIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        try:
            HOST, PORT = self._get_host_and_port()
            print(HOST, PORT)

            connection = http.client.HTTPSConnection(HOST, PORT, context=ssl._create_unverified_context())
            body = urllib.parse.urlencode({'username': self.integration.username, 'password': self.integration.password})
            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
                'Content-Length': str(len(body)),
                'Host': HOST,
                'User-Agent': "apicalls_httplib.py/1.0",
                'Accept': "*/*"
            }
            try:
                connection.request("POST", "/services/auth/login", body, headers)
            except ConnectionRefusedError:
                return {"success": False, "error": "Connection failed"}
            response = connection.getresponse()
            if response.status == 200:
                return {"success": True}
            else:
                return {"success": False, "error": response.reason}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is unreachable"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_forms():
        return {
            "label": "Splunk",
            "type": "form",
            "children": [
                {
                    "name": "host_url",
                    "type": "text/url",
                    "label": "TCP Management HOST URL",
                    "placeholder": "https://example.com:8089",
                    "required": True,
                },
                {
                    "name": "username",
                    "type": "text",
                    "label": "Username",
                    "placeholder": "Enter your Splunk Username",
                    "required": True,
                },
                {
                    "name": "password",
                    "type": "text/password",
                    "label": "Password",
                    "placeholder": "Enter your Splunk Password",
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return SplunkIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.STEAMPIPE,
            ConnectionInterfaces.REST_API,
            ConnectionInterfaces.PYTHON_SDK
        ]

    def generate_steampipe_creds(self) -> SteampipeCreds:
        creds = self._temp_credentials()
        conf_path = "~/.steampipe/config/splunk.spc"
        config = """connection "splunk" {
  plugin = "splunk"
}
"""
        return SteampipeCreds(
            envs=creds,
            plugin_name="splunk",
            connection_name="splunk",
            conf_path=conf_path,
            config=config,
        )

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        client = importlib.import_module(
            client_definitions[0].import_library_names[0], package=None
        )
        HOST, PORT = self._get_host_and_port()
        try:
            splunk = client.connect(
                host=HOST,
                port=PORT,
                token=payload_task.creds.envs.get("SPLUNK_AUTH_TOKEN"),
                autologin=True,
            )
        except Exception as e:
            logger.exception(f"Failed to connect to Splunk with error {str(e)}")
            splunk = None
        return [
            {
                "clients": {
                    "splunk": splunk
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = self._temp_credentials()
        return SDKCreds(envs=creds)

    def _temp_credentials(self):
        try:
            sessionKey = None
            HOST, PORT = self._get_host_and_port()
            connection = http.client.HTTPSConnection(HOST, PORT, context=ssl._create_unverified_context())
            body = urllib.parse.urlencode({'username': self.integration.username, 'password': self.integration.password})
            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
                'Content-Length': str(len(body)),
                'Host': HOST,
                'User-Agent': "apicalls_httplib.py/1.0",
                'Accept': "*/*"
            }
            connection.request("POST", "/services/auth/login", body, headers)
            response = connection.getresponse()
            if response.status != 200:
                connection.close()
                logger.exception(f"{response.status} ({response.reason})")
            else:
                body = response.read()
                sessionKey = ElementTree.XML(body).findtext("./sessionKey")
        except BaseException as e:
            logger.error(f"Cannot Generate credentials for this task, Failed with error {str(e)}")
            return {}
        return {
            "SPLUNK_URL": self.integration.host_url,
            "SPLUNK_AUTH_TOKEN": sessionKey
        }

    def _get_host_and_port(self):
        # Extracting HOST and PORT from host_url
        HOST = self.integration.host_url.split(":")[1][2:]
        PORT = (
            8089
            if len(self.integration.host_url.split(":")) == 2
            else self.integration.host_url.split(":")[-1]
        )
        return HOST, PORT
