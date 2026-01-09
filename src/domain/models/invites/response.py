from uuid import UUID
from pydantic import BaseModel, ConfigDict

from ..core.response import ServerListResponse
from ..member.response import MemberResponse, ReducedMemberResponse


class InviteAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    key: str
    inviter: MemberResponse
    use_limit: int

class InviteKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inviter: ReducedMemberResponse
    server: ServerListResponse