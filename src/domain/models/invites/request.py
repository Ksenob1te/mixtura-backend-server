from uuid import UUID
from pydantic import BaseModel

from ..request import AccessDataRequest


class GetInviteByKeyRequest(BaseModel):
    key: str

class UseInviteRequest(BaseModel):
    user_id: UUID
    restriction_mask: int
    
    nickname: str
    key: str

class GetInviteListRequest(BaseModel):
    access_data: AccessDataRequest
    
    server_id: UUID

class InviteCreateRequest(BaseModel):
    access_data: AccessDataRequest

    use_limit: int | None = None

class RevokeInviteRequest(BaseModel):
    access_data: AccessDataRequest
    
    invite_id: UUID