from typing import List, Optional, Any, Union

from pydantic import BaseModel, SerializeAsAny, field_validator, ValidationError

from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.models import (
    BaseCreds,
    ConnectionInterfaces,
)
import inspect
import os


class Caller(BaseModel):
    user_id: str
    root_user_id: str


class ExecutionDetails(BaseModel):
    execution_id: str
    bot_id: str
    bot_name: str
    node_name: str
    caller: Caller


class PayloadTaskContext(BaseModel):
    integration: SerializeAsAny[IntegrationSchema]
    global_variables: dict = {}  # Global Variables defined by User, this will be store in secret manager
    integration_variables: dict = {}  # Secret manager variables stored for the specific Integration.
    integration_group_vars: dict = {}  # Secret manager variables stored for the specific Integration Group.
    execution_details: ExecutionDetails
    node_steps: dict

    @field_validator('integration', mode='before')
    @classmethod
    def validate_integration(cls, integration):
        if isinstance(integration, dict):
            for base_schema in IntegrationSchema.__subclasses__():
                for subclass in base_schema.__subclasses__():
                    dir_name = os.path.dirname(inspect.getfile(subclass)).split('/')[-1]
                    if dir_name == integration['cspName']:
                        return subclass(**integration)
        return integration


class PayloadTask(BaseModel):
    task_id: Optional[str]
    creds: SerializeAsAny[BaseCreds]
    connection_interface: ConnectionInterfaces
    executable: str
    clients: Optional[List[str]] = None
    params: Optional[Any] = None
    node_details: Optional[Any] = None
    context: PayloadTaskContext
    resources: Optional[List] = None

    @field_validator('creds', mode='before')
    @classmethod
    def validate_creds(cls, creds: dict):
        if isinstance(creds, dict):
            for sub_cls in BaseCreds.__subclasses__():
                if sub_cls.connection_interface.value == creds['creds_type']:
                    return sub_cls(**creds)
        return creds


class Payload(BaseModel):
    job_id: str
    state: Optional[dict] = None
    tasks: List[PayloadTask]


class ResponseError(BaseModel):
    message: str
    other_details: dict = None


class ResponseDebugInfo(BaseModel):
    executable: str
    job_type: str
    resource_type: str = None
    environs: dict = None


class TaskResult(BaseModel):
    task_id: str
    integration_id: str
    integration_type: str
    resources: Optional[List] = None
    errors: Optional[List[ResponseError]] = None
    debug_info: ResponseDebugInfo


class JobResult(BaseModel):
    job_id: str
    task_results: List[TaskResult]
