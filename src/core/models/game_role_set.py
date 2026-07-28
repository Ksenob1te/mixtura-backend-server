from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GameRoleSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_global: bool
    server_id: UUID | None = None


class GameRoleSetCreate(BaseModel):
    name: str
    is_global: bool = False
    server_id: UUID | None = None


class GameRoleSetUpdate(BaseModel):
    id: UUID
    name: str | None = None
