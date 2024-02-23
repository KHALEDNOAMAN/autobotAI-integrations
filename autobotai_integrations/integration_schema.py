from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ConnectionTypes(Enum):
    DIRECT = "DIRECT"
    AGENT = "AGENT"


class IntegrationStates(Enum):
    ACTIVE = "ACTIVE"  # Accessible
    INACTIVE = "INACTIVE"  # In-Accessible
    AGENT_UPDATE_REQUIRED = "AGENT_UPDATE_REQUIRED"


class IntegrationSchema(BaseModel):
    userId: str
    accountId: str
    integrationState: IntegrationStates = IntegrationStates.INACTIVE.value
    cspName: str
    alias: str
    connection_type: ConnectionTypes = ConnectionTypes.DIRECT.value
    groups: list = []
    agent_ids: list = []
    accessToken: str = ""
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    indexFailures: int = 0
    isUnauthorized: bool = False
    lastUsed: Optional[str] = None
    resource_type: str = 'integration'
    activeRegions: Optional[list] = None

    @classmethod
    def encryption_exclusions(self):
        return ["agent_ids"]
