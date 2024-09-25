from enum import Enum
from typing import List, Optional, Any, Union

from pydantic import BaseModel, SerializeAsAny, field_validator, Field, model_validator

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


class JobSizes(str, Enum):
    MICRO = "Micro"
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"

    def __str__(self):
        return self.value


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


class Param(BaseModel):
    params_type: str = Field(alias="type")
    name: str
    ai_generated: bool = False
    required: bool = False
    values: Optional[Any] = None
    filter_relevant_resources: bool = False

    def model_dump_json(self, *args, **kwargs) -> str:
        kwargs["by_alias"] = True
        return super().model_dump_json(*args, **kwargs)

    @model_validator(mode="before")
    @classmethod
    def resource_type_validator(cls, values: Any) -> Any:
        if not values.get("params_type", None) and values.get("type", None):
            values["params_type"] = values["type"]
        if not values.get("type", None) and values.get("params_type", None):
            values["type"] = values["params_type"]
        return values


class PayloadTask(BaseModel):
    task_id: Optional[str]
    creds: SerializeAsAny[BaseCreds]
    connection_interface: ConnectionInterfaces
    executable: str
    tables: Optional[List[str]] = None
    clients: Optional[List[str]] = None
    params: Optional[List[Param]] = []
    node_details: Optional[Any] = None
    context: PayloadTaskContext

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
    output_url: Optional[dict] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    job_size: Union[JobSizes, str] = None


class ResponseError(BaseModel):
    message: str
    other_details: Optional[dict] = None


class ResponseDebugInfo(BaseModel):
    executable: str
    job_type: str
    resource_type: Optional[str] = None
    environs: Optional[dict] = None


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
