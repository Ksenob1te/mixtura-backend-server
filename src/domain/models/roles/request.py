from uuid import UUID

from pydantic import BaseModel

from .response import PermissionResponse

from ..request import AccessDataRequest


class ListServerRolesRequest(BaseModel):
    access_data: AccessDataRequest


class CreateServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    name: str
    position: int


class UpdateServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID

    name: str | None
    position: int | None


class UpdateServerRolePermissionsRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID
    target_permissions_ids: list[UUID]


class DeleteServerRoleRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID
