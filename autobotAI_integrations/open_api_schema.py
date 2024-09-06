from typing import Optional, List, Any

from pydantic import BaseModel
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import Param

class OpenAPIPathParams(Param):
    data_type: Optional[str] = None
    description: Optional[str] = None
    default: Any = None
    example: Any = None


class OpenAPIAction(BaseModel):
    resource_type: str = "action"
    name: str
    root_user_id: str = None
    user_id: str = None
    code: str
    integration_type: str
    clients: Optional[List[str]] = None
    executable_type: Optional[str] = ConnectionInterfaces.REST_API.value
    category: Optional[str] = None
    parameters_definition: Optional[List[OpenAPIPathParams]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
