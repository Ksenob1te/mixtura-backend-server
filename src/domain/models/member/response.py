from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# class ServerPermissionResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#
#     id: UUID
#     code_name: str


class ServerRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    position: int
    permission_mask: int


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    user_id: UUID | None
    joined_at: datetime
    server_role: ServerRoleResponse | None


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
