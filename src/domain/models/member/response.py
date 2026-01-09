from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from ..roles.response import PermissionResponse, ServerRoleResponse


# class ServerPermissionResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     id: UUID
#     code_name: str



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

    permissions: list[str]
    restrictions: list[MemberRestrictionResponse]