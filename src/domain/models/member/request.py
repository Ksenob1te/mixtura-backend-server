from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from ..request import AccessDataRequest


class GetMemberByUserRequest(BaseModel):
    server_id: UUID
    user_id: UUID


class GetMemberListRequest(BaseModel):
    access_data: AccessDataRequest


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
