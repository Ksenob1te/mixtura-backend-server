from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServerRole(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    server_id: UUID
    name: str
    position: int


class ServerRoleCreate(BaseModel):
    server_id: UUID
    name: str
    position: int = 0


class ServerRoleUpdate(BaseModel):
    id: UUID
    name: str | None = None
    position: int | None = None
