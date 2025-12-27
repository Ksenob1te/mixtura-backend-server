from uuid import UUID

from pydantic import BaseModel

from ..request import AccessDataRequest


class ListServerRolesRequest(BaseModel):
    access_data: AccessDataRequest

class CreateServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    name: str
    position: int
    permission_mask: int

class UpdateServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    name: str | None
    position: int | None
    target_permission_mask: int | None

class DeleteServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID