from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app.rabbit.models.base import AccessDataRequest
from src.app.rabbit.models.member import MemberResponse, ReducedMemberResponse
from src.app.rabbit.models.server import ServerListResponse


class GetUserRestrictionRequest(BaseModel):
    user_id: UUID
    server_id: UUID


class GetInviteByKeyRequest(BaseModel):
    key: str


class UseInviteRequest(BaseModel):
    user_id: UUID
    restriction_mask: int
    nickname: str
    key: str


class GetInviteListRequest(BaseModel):
    access_data: AccessDataRequest


class InviteCreateRequest(BaseModel):
    access_data: AccessDataRequest
    use_limit: int | None = None


class RevokeInviteRequest(BaseModel):
    access_data: AccessDataRequest
    invite_id: UUID


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
