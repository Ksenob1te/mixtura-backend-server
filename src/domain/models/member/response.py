from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from ..roles.response import ServerRoleResponse


# class ServerPermissionResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     id: UUID
#     code_name: str


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    user_id: UUID | None
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
    type_code: str


class MemberRestrictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reason: str
    expiration_date: datetime
    restriction: RestrictionResponse
