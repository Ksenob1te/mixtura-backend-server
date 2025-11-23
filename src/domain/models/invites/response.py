from uuid import UUID
from pydantic import BaseModel, ConfigDict

from src.domain.models.core.response import ServerListResponse


class InviteAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    inviter_id: UUID
    use_limit: int

class InviteKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    server: ServerListResponse