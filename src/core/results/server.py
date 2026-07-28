from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ServerListResult(BaseModel):
    id: UUID
    name: str
    description: str
    icon_id: UUID | None = None
    banner_id: UUID | None = None
    owner_id: UUID
    public: bool
    created_at: datetime

class ServerDetailResult(ServerListResult):
    pass
