import base64
from enum import Enum
from typing import List, Optional, Type, Union
from urllib.parse import urlparse, urlunparse

import boto3
from pydantic import Field, field_validator, model_validator
from autobotAI_integrations import BaseService
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations.models import (
    BaseSchema,
    ConnectionInterfaces,
    IntegrationCategory,
    RestAPICreds,
    SDKClient,
    SDKCreds,
)
from autobotAI_integrations.payload_schema import PayloadTask
from autobotAI_integrations.utils.boto3_helper import Boto3Helper
from autobotAI_integrations.utils.logging_config import logger


class OpensearchAuthTypes(str, Enum):
    AWS_CONFIG = "aws_config"
    DIRECT_AUTH = "direct_auth"


class AWSOpensearchType(str, Enum):
    AWS_OPENSEARCH_SERVICE = "aws_opensearch_service"
    OPENSEARCH_SERVERLESS = "opensearch_serverless"


class OpensearchIntegration(BaseSchema):
    host_url: Optional[str] = None

    # On-premise Opensearch
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = Field(default=None, exclude=True)
    verify_cert: bool = Field(default=True)

    # AWS Opensearch Service
    region: Optional[str] = None
    opensearch_type: Optional[AWSOpensearchType] = None
    access_key: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)
    session_token: Optional[str] = Field(default=None, exclude=True)
    account_id: Optional[str] = None
    roleArn: Optional[str] = None
    externalId: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Opensearch"
    category: Optional[str] = IntegrationCategory.MONITORING_TOOLS.value
    description: Optional[str] = (
        "OpenSearch is a community-driven, open-source search and analytics suite, based on Elasticsearch and Kibana, designed for scalability and flexibility in search applications."
    )

    def use_dependency(self, dependency: dict):
        if dependency.get("cspName") == "aws":
            self.roleArn = dependency.get("roleArn")
            self.access_key = dependency.get("access_key")
            self.secret_key = dependency.get("secret_key")
            self.session_token = dependency.get("session_token")
            self.externalId = dependency.get("externalId")
            self.account_id = dependency.get("account_id")
        elif dependency.get("cspName") in ["linux", "kubernetes"]:
            self.connection_type = ConnectionTypes.AGENT
            self.agent_ids = dependency.get("agent_ids")
            self.dependent_integration_id = dependency.get("accountId")

    @field_validator("host_url", mode="before")
    @classmethod
    def validate_host_url(cls, host_url):
        return host_url.strip("/")

    @model_validator(mode="before")
    @classmethod
    def validate_host_and_port(cls, values):
        host_url = values.get("host_url")
        port = values.get("port")

        if host_url:

            parsed_url = urlparse(host_url)

            if not port and parsed_url.port:
                values["port"] = parsed_url.port
            elif not port:
                # Set default ports based on scheme
                if parsed_url.scheme == 'https':
                    values["port"] = 443
                elif parsed_url.scheme == 'http':
                    values["port"] = 80

            # Remove port from host_url if it exists
            cleaned_netloc = parsed_url.hostname
            cleaned_url = urlunparse(
                (
                    parsed_url.scheme,
                    cleaned_netloc,
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )
            values["host_url"] = cleaned_url

            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid host_url format")

        return values


class OpensearchService(BaseService):
    def __init__(self, ctx: dict, integration: Union[OpensearchIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, OpensearchIntegration):
            integration = OpensearchIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_aws_credentials(self):
        if self.integration.roleArn not in ["None", None]:
            boto3_helper = Boto3Helper(
                self.ctx, integration=self.integration.dump_all_data()
            )
            return boto3_helper.get_session().get_credentials()
        else:
            return boto3.Session(
                aws_access_key_id=self.integration.access_key,
                aws_secret_access_key=self.integration.secret_key,
                region_name=self.integration.region,
                aws_session_token=self.integration.session_token if self.integration.session_token else None,
            ).get_credentials()

    def _test_integration(self):
        try:
            from opensearchpy import (
                AuthorizationException,
                OpenSearch,
                RequestsHttpConnection,
                AWSV4SignerAuth,
            )
            logger.info(f"Initiating test for integration: {self.integration.accountId}")
            host = self.integration.host_url.split("://")[1]
            use_ssl = self.integration.host_url.split("://")[0] == "https"
            client = None
            if self.integration.auth_type == OpensearchAuthTypes.AWS_CONFIG.value:
                service = "es" if AWSOpensearchType.AWS_OPENSEARCH_SERVICE.value == self.integration.opensearch_type else "aoss"
                logger.info(
                    f"Accessing service: {service} for {self.integration.opensearch_type}"
                )
                auth = AWSV4SignerAuth(
                    self._get_aws_credentials(),
                    self.integration.region,
                    service,
                )
                client = OpenSearch(
                    hosts=[{"host": host, "port": self.integration.port}],
                    http_auth=auth,
                    use_ssl=use_ssl,
                    verify_certs=self.integration.verify_cert,
                    connection_class=RequestsHttpConnection,
                    pool_maxsize=20,
                    timepout=3,
                )
            elif self.integration.auth_type == OpensearchAuthTypes.DIRECT_AUTH.value:
                if self.integration.connection_type == ConnectionTypes.AGENT:
                    return {"success": True}
                auth = (self.integration.username, self.integration.password)
                client = OpenSearch(
                    hosts=[{"host": host, "port": self.integration.port}],
                    http_auth=auth,
                    use_ssl=use_ssl,
                    verify_certs=self.integration.verify_cert,
                    timeout=3
                )
            else:
                return {"success": False, "error": "Invalid Authentication Method."}
            logger.info(str(client.info()))
            return {"success": True}
        except AuthorizationException as e:
            return {"success": False, "error": str(e.error)}
        except Exception as e:
            logger.error(str(e))
            return {"success": False, "error": "Request failed with unexpected error"}

    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        from opensearchpy import (
            OpenSearch,
            RequestsHttpConnection,
            AWSV4SignerAuth,
        )
        host = payload_task.creds.envs.get("OPENSEARCH_HOST_URL").split("://")[1]
        use_ssl = (
            payload_task.creds.envs.get("OPENSEARCH_HOST_URL").split("://")[0]
            == "https"
        )
        client = None
        if self.integration.auth_type == OpensearchAuthTypes.AWS_CONFIG.value:
            service = (
                "es"
                if AWSOpensearchType.AWS_OPENSEARCH_SERVICE.value
                == self.integration.opensearch_type
                else "aoss"
            )
            credentials = boto3.Session(
                aws_access_key_id=payload_task.creds.envs.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=payload_task.creds.envs.get(
                    "AWS_SECRET_ACCESS_KEY"
                ),
                aws_session_token=payload_task.creds.envs.get("AWS_SESSION_TOKEN"),
            ).get_credentials()
            auth = AWSV4SignerAuth(
                credentials, self.integration.region, service=service
            )
            client = OpenSearch(
                hosts=[{"host": host, "port": self.integration.port}],
                http_auth=auth,
                use_ssl=use_ssl,
                verify_certs=self.integration.verify_cert,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20,
            )
        elif self.integration.auth_type == OpensearchAuthTypes.DIRECT_AUTH.value:
            auth = (
                payload_task.creds.envs.get("OPENSEARCH_USERNAME"),
                payload_task.creds.envs.get("OPENSEARCH_PASSWORD"),
            )
            client = OpenSearch(
                hosts=[
                    {
                        "host": host,
                        "port": int(payload_task.creds.envs.get("OPENSEARCH_URL_PORT")),
                    }
                ],
                http_auth=auth,
                use_ssl=use_ssl,
                verify_certs=self.integration.verify_cert,
            )
        return [
            {
                "clients": {
                    "opensearch": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context,
            }
        ]

    @staticmethod
    def get_forms():
        return {
            "label": "Opensearch",
            "type": "form",
            "children": [
                {
                    "label": "AWS Opensearch Integration",
                    "type": "form",
                    "formId": OpensearchAuthTypes.AWS_CONFIG.value,
                    "children": [
                        {
                            "name": "host_url",
                            "type": "text/url",
                            "label": "Host URL",
                            "placeholder": "Enter the host URL",
                            "required": True,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "dataType": "integration",
                            "integrationType": "aws",
                            "label": "Route Through Agent (Optional)",
                            "placeholder": "Enter Integration Id",
                            "description": "Select Account you want to install this integration",
                            "required": True,
                        },
                        {
                            "name": "opensearch_type",
                            "type": "select",
                            "label": "Select OpenSearch Deployment Type",
                            "placeholder": "Choose your OpenSearch deployment",
                            "description": "Please select whether you are using Amazon OpenSearch Service or OpenSearch Serverless for your integration.",
                            "options": [
                                {
                                    "label": "Amazon OpenSearch Service",
                                    "value": AWSOpensearchType.AWS_OPENSEARCH_SERVICE.value,
                                },
                                {
                                    "label": "OpenSearch Serverless",
                                    "value": AWSOpensearchType.OPENSEARCH_SERVERLESS.value,
                                },
                            ],
                            "required": True,
                        },
                        {
                            "name": "region",
                            "type": "text",
                            "label": "Region",
                            "placeholder": "example: us-east-1",
                            "required": True,
                        },
                        {
                            "name": "verify_cert",
                            "type": "select",
                            "label": "Verify SSL Certificate",
                            "description": "Enable/disable SSL certificate verification",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "default": True,
                        },
                    ],
                },
                {
                    "label": "On-Premises Integration",
                    "type": "form",
                    "formId": OpensearchAuthTypes.DIRECT_AUTH.value,
                    "children": [
                        {
                            "name": "host_url",
                            "type": "text/url",
                            "label": "Host URL",
                            "placeholder": "Enter the OpenSearch host URL:PORT (e.g., http://localhost:9200)",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "Username",
                            "placeholder": "Enter your username",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Password",
                            "placeholder": "Enter your password",
                            "required": True,
                        },
                        {
                            "name": "integration_id",
                            "type": "select",
                            "integrationType": "linux,kubernetes",
                            "dataType": "integration",
                            "label": "Route Through Agent (Optional)",
                            "placeholder": "Enter Integration Id",
                            "description": "Select an integration with a Linux or Kubernetes agent to route this connection through it. Leave blank/None to connect directly.",
                            "required": False,
                        },
                        {
                            "name": "verify_cert",
                            "type": "select",
                            "label": "Verify SSL Certificate",
                            "placeholder": "Default: True",
                            "description": "Enable/disable SSL certificate verification",
                            "options": [
                                {"label": "True", "value": True},
                                {"label": "False", "value": False},
                            ],
                            "default": True,
                        },
                    ],
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return OpensearchIntegration

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
            ConnectionInterfaces.REST_API
        ]

    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {}
        if self.integration.auth_type == OpensearchAuthTypes.AWS_CONFIG.value:
            if self.integration.roleArn not in ["None", None]:
                boto3_helper = Boto3Helper(
                    self.ctx, integration=self.integration.model_dump()
                )
                envs = {
                    "AWS_ACCESS_KEY_ID": boto3_helper.get_access_key(),
                    "AWS_SECRET_ACCESS_KEY": boto3_helper.get_secret_key(),
                    "AWS_SESSION_TOKEN": boto3_helper.get_session_token(),
                }
            else:
                envs = {
                    "AWS_ACCESS_KEY_ID": str(self.integration.access_key),
                    "AWS_SECRET_ACCESS_KEY": str(self.integration.secret_key),
                }
                if self.integration.session_token not in [None, "None"]:
                    envs["AWS_SESSION_TOKEN"] = str(self.integration.session_token)
            envs.update({
                "OPENSEARCH_HOST_URL": self.integration.host_url,
                "OPENSEARCH_URL_PORT": str(443)
            })
        else:
            envs = {
                "OPENSEARCH_HOST_URL": self.integration.host_url,
                "OPENSEARCH_URL_PORT": str(self.integration.port),
                "OPENSEARCH_USERNAME": self.integration.username,
                "OPENSEARCH_PASSWORD": self.integration.password,
            }
        return SDKCreds(envs=envs)
    
    def generate_rest_api_creds(self) -> RestAPICreds:
        encoded_credentials = base64.b64encode(
            f"{self.integration.username}:{self.integration.password}".encode("utf-8")
        ).decode("utf-8")
        return RestAPICreds(
            base_url=f"{self.integration.host_url}:{self.integration.port}",
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            verify_ssl=self.integration.verify_cert,
        ) 
