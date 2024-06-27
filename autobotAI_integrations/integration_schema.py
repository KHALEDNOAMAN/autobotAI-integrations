from enum import Enum
from typing import Optional
from typing import Optional, Any, get_origin, get_args, Union
from pydantic import BaseModel, ConfigDict, ValidationError, Field, validator, model_validator
import uuid

class ConnectionTypes(str, Enum):
    DIRECT = "DIRECT"
    AGENT = "AGENT"

    def __str__(self):
        return self.value


class IntegrationStates(str, Enum):
    ACTIVE = "ACTIVE"  # Accessible
    INACTIVE = "INACTIVE"  # In-Accessible
    AGENT_UPDATE_REQUIRED = "AGENT_UPDATE_REQUIRED"

    def __str__(self):
        return self.value


class IntegrationSchema(BaseModel):
    userId: str  # The user creating the Integration
    accountId: str  # Unique ID for the integration, For AWS it is Account ID, Azure it is subscription id and GCP it is project id, if no unique id available we generate an unique id.
    integrationState: IntegrationStates = IntegrationStates.INACTIVE.value
    cspName: str  # AWS, AZURE, GCP, GITLAB etc.
    alias: str  # Name given by User
    connection_type: ConnectionTypes = ConnectionTypes.DIRECT.value  # Direct means we get the credentials, Agent means we don't have the creds, our agent is installed in the customer's environment.
    groups: list = []  # Tags/groups
    agent_ids: list = []  # If agent based, then agent ids are populated
    accessToken: str = ""  # Part of creds
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    indexFailures: int = 0
    isUnauthorized: bool = False
    lastUsed: Optional[str] = None
    resource_type: str = 'integration'

    def __init__(self, **kwargs: Any):
        if not kwargs.get("accountId"):
            kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)
    
    class Config:
        extra = "allow"

    @model_validator(mode="before")
    @classmethod
    def coerce_to_str(cls, values: Any) -> Any:
        for field in cls.model_fields:
            annotation = cls.model_fields[field].annotation                        
            if annotation == str or (get_origin(annotation) in [Optional, Union] and str in get_args(annotation)):
                if field in values:
                    values[field] = str(values[field])
        return values

    @classmethod
    def encryption_exclusions(self):
        return ["agent_ids"]

    def dump_all_data(self):
        excluded =[key for key, val in  self.__class__.model_fields.items() if val.exclude]
        raw_dict =  self.model_dump()
        for key in excluded:
            raw_dict[key] = getattr(self, key)
        return raw_dict
