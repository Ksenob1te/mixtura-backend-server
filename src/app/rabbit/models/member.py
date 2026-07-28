from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app.rabbit.models.base import AccessDataRequest, PaginationRequest
from src.app.rabbit.models.role import PermissionResponse, ServerRoleResponse


class GetMemberByUserRequest(BaseModel):
    server_id: UUID
    user_id: UUID


class GetMemberListRequest(BaseModel):
    access_data: AccessDataRequest
    pagination: PaginationRequest
    nickname_filter: str = ""


class JoinServerRequest(BaseModel):
    server_id: UUID
    user_id: UUID
    restriction_mask: int
    nickname: str


class VirtualMemberCreateRequest(BaseModel):
    access_data: AccessDataRequest
    nickname: str


class MemberGetInfoRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID


class MemberPermissionRequest(BaseModel):
    access_data: AccessDataRequest


class MemberUpdateRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID
    name: str | None = None
    server_role_id: UUID | None = None


class KickMemberRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID


class MemberMigrationRequest(BaseModel):
    access_data: AccessDataRequest
    origin_member_id: UUID
    target_member_id: UUID


class GetMemberRestrictionsRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID


class AddMemberRestrictionRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID
    reason: str
    expiration_date: datetime
    restriction_id: UUID


class RemoveMemberRestrictionRequest(BaseModel):
    access_data: AccessDataRequest
    target_member_id: UUID
    member_restriction_id: UUID


class ReducedMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nickname: str
    user_id: UUID | None


class MemberResponse(ReducedMemberResponse):
    model_config = ConfigDict(from_attributes=True)
    server_id: UUID
    joined_at: datetime
    server_role: ServerRoleResponse | None


class AccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member: MemberResponse | None
    permission_mask: int
    restriction_mask: int


class RestrictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str


class MemberRestrictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    reason: str
    expiration_date: datetime
    restriction: RestrictionResponse


class MemberPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    permissions: list[PermissionResponse]
    restrictions: list[MemberRestrictionResponse]
