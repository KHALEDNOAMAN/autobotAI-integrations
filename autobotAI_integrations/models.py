from enum import Enum
from typing import Optional, List, Any, Dict, ClassVar

from pydantic import BaseModel, ConfigDict

from autobotAI_integrations import IntegrationV2Schema


class ConnectionInterfaces(str, Enum):
    STEAMPIPE = 'steampipe'
    PYTHON_SDK = 'python_sdk'
    REST_API = 'rest_api'
    CLI = 'cli'

    def __str__(self):
        return self.value


class BaseCreds(BaseModel):
    pass


class SteampipeCreds(BaseCreds):
    connection_interface: ClassVar[ConnectionInterfaces] = ConnectionInterfaces.STEAMPIPE
    creds_type: str = ConnectionInterfaces.STEAMPIPE.value
    envs: dict
    connection_name: str
    plugin_name: str
    conf_path: Optional[str] = str
    config: Optional[str] = None
    tables: list = []


class RestAPICreds(BaseCreds):
    connection_interface: ClassVar[ConnectionInterfaces] = ConnectionInterfaces.REST_API
    creds_type: str = ConnectionInterfaces.REST_API.value
    api_url: str
    token: str
    headers: dict


class Client(BaseModel):
    name: str


class SDKClient(Client):
    model_config = ConfigDict(extra='allow')
    pip_package_names: Optional[List[str]] = None
    import_library_names: Optional[List[str]] = None


class SDKCreds(BaseCreds):
    connection_interface: ClassVar[ConnectionInterfaces] = ConnectionInterfaces.PYTHON_SDK
    creds_type: str = ConnectionInterfaces.PYTHON_SDK.value
    creds: Optional[dict] = None
    envs: Optional[dict] = None



class CLICreds(BaseCreds):
    connection_interface: ClassVar[ConnectionInterfaces] = ConnectionInterfaces.CLI
    creds_type: str = ConnectionInterfaces.CLI.value
    envs: dict
    installer_check: str
    install_command: str


# Setting default to None
class BaseSchema(IntegrationV2Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
