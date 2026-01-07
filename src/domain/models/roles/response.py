from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str

class ServerRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    position: int
    permissions_list: list[PermissionResponse]