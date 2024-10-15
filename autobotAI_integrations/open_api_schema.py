from typing import Optional, List, Any

from pydantic import BaseModel, Field, model_validator
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import Param

class OpenAPIPathParams(Param):
    in_: Optional[str] = Field(default=None, alias="in")
    description: Optional[str] = None
    default: Any = None
    example: Any = None

    @model_validator(mode="before")
    @classmethod
    def resource_type_validator(cls, values: Any) -> Any:
        if not values.get("params_type", None) and values.get("type", None):
            values["params_type"] = values["type"]
        if not values.get("type", None) and values.get("params_type", None):
            values["type"] = values["params_type"]
        if not values.get("in", None) and values.get("in_", None):
            values["in"] = values["in_"]
        if not values.get("in_", None) and values.get("in", None):
            values["in_"] = values["in"]
        return values


class OpenAPIAction(BaseModel):
    resource_type: str = "action"
    name: str
    root_user_id: str = None
    user_id: str = None
    code: str
    integration_type: str
    clients: Optional[List[str]] = []
    executable_type: Optional[str] = ConnectionInterfaces.REST_API.value
    category: Optional[str] = None
    parameters_definition: Optional[List[OpenAPIPathParams]] = []


class OpenAPIPathModel(BaseModel):
    path_url: str
    method: str
    summary: Optional[str] = ""
    description: Optional[str] = ""
    parameters: List[OpenAPIPathParams] = []

    def __init__(self,*args ,**kwargs):
        if "method" in kwargs:
            kwargs["method"] = kwargs["method"].upper()
        super().__init__(*args, **kwargs)


class OpenAPISchema(BaseModel):
    version: str  # openapi, swagger
    base_url: Optional[str] = "{base_url}"  # servers or host
    tags: Optional[List[dict]] = None
    paths: List[OpenAPIPathModel] = []
    security: Optional[List[dict]] = None
    components: dict = dict()
