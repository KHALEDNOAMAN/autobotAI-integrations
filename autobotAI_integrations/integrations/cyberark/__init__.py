from typing import Optional, Union ,List
from pydantic import Field,field_validator
import requests
import re
import importlib

from autobotAI_integrations import BaseService
from autobotAI_integrations.integration_schema import ConnectionTypes
from autobotAI_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds , \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient
from autobotAI_integrations.models import IntegrationCategory, MCPCreds

class CyberArkIntegration(BaseSchema):
    base_url: str = Field(default=None, description="Identity Tenant URL")
    username: Optional[str] = Field(default=None, exclude=False)
    password: Optional[str] = Field(default=None, exclude=True)
    name: Optional[str] = "CyberArk"
    category: Optional[str] = IntegrationCategory.SECURITY_TOOLS.value
    description: Optional[str] = (
        "CyberArk is a leading identity security platform that protects critical assets by controlling and monitoring privileged access."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, base_url) -> Optional[str]:
        identityTenantURL = r"^https://[\w.-]+\.id\.cyberark\.cloud/?$"
        if base_url and base_url != "None":
            if re.match(identityTenantURL, base_url):
                return base_url.strip("/")
            raise ValueError(f"Invalid CyberArk Identity Tenant URL: {base_url}. Format: https://example.id.cyberark.cloud")
        raise ValueError("CyberArk Identity Tenant URL is required")

class CyberArkService(BaseService):
    def __init__(self,ctx:dict,integration:Union[CyberArkIntegration,dict]):
        if not isinstance(integration,CyberArkIntegration):
            integration=CyberArkIntegration(**integration)
        super().__init__(ctx,integration)

    def _test_integration(self):
        try:
            headers={
                "Content-Type":"application/x-www-form-urlencoded"
            }

            user_endpoint = f"{self.integration.base_url}/oauth2/platformtoken/"
            response = requests.post(user_endpoint, headers=headers,data={
            "grant_type":"client_credentials",
            "client_id": self.integration.username,
            "client_secret": self.integration.password
            })
            if response.status_code == 200:
                return {"success": True}
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed. Please check your UserName and PassWord."
                }
            elif response.status_code == 404:
                return {
                "success": False,
                "error": "Error: Not Found. Invalid CyberArk Indentity URL",
                }
            else:
                return {
                    "success": False,
                    "error": f"Authentication failed with status code: {response.status_code}",
                }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
            
    @staticmethod
    def get_forms():
        return {
            "label": "CyberArk",
            "type": "form",
            "childern" : [
                {
                    "label": "CyberArk Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "base_url",
                            "type": "text/url",
                            "label": "CyberArk Indentity URL",
                            "placeholder": "https://example.id.cyberark.cloud",
                            "description": "Your CyberArk Indentity URL",
                            "required": True,
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "label": "ClientId",
                            "placeholder": "Enter your ClientId Of CyberArk",
                            "required": True,
                        },
                        {
                            "name": "password",
                            "type": "text/password",
                            "label": "Client Secret",
                            "placeholder": "Enter your Client's Secret Of CyberArk",
                            "required": True,
                        },
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_schema(ctx=None):
        return CyberArkIntegration
    
    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK,ConnectionInterfaces.REST_API]
    
    def build_python_exec_combinations_hook(
        self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        from ark_sdk_python.auth import ArkISPAuth
        from ark_sdk_python.models.auth.ark_auth_profile import ArkAuthProfile
        from ark_sdk_python.models.auth.ark_auth_method import ArkAuthMethod, IdentityArkAuthMethodSettings
        from ark_sdk_python.models.auth.ark_secret import ArkSecret
        
        clients_classes = dict()
        
        isp_auth = ArkISPAuth()
        isp_auth.authenticate(
            auth_profile=ArkAuthProfile(
                username=payload_task.creds.envs.get("CYBERARK_USERNAME"),
                auth_method=ArkAuthMethod.Identity,
                auth_method_settings=IdentityArkAuthMethodSettings()
            ),
            secret=ArkSecret(secret=payload_task.creds.envs.get("CYBERARK_PASSWORD"))
        )
        
        for client in client_definitions:
            try:
                client_module = importlib.import_module(client.module, package=None)
                
                if not client.class_name:
                    clients_classes[client.name] = client_module
                    continue
                
                if hasattr(client_module, client.class_name):
                    cls = getattr(client_module, client.class_name)
                    try:
                        clients_classes[client.name] = cls(isp_auth)
                    except TypeError:
                        clients_classes[client.name] = cls(isp_auth=isp_auth)
            except BaseException as e:
                print(f"Error initializing client {client.name}: {e}")
                continue
        
        return [
            {
                "clients": clients_classes,
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]
    
    def generate_python_sdk_creds(self) -> SDKCreds:
        envs = {
            "CYBERARK_USERNAME": self.integration.username,
            "CYBERARK_PASSWORD": self.integration.password,
        }
        return SDKCreds(envs=envs)
    
    def generate_rest_api_creds(self):
        headers={
                "Content-Type":"application/x-www-form-urlencoded"
        }

        user_endpoint = f"{self.integration.base_url}/oauth2/platformtoken/"
        response = requests.post(user_endpoint, headers=headers,data={
        "grant_type":"client_credentials",
        "client_id": self.integration.username,
        "client_secret": self.integration.password
        })
        data = response.json()
        token = data.get('access_token')
        return RestAPICreds(
            base_url=self.integration.base_url,
            headers={
                "Authorization": f"Bearer {token}",
            }
        )
    
        

    