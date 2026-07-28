from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GameRole(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role_set_id: UUID
    icon_id: UUID | None = None
    min_in_team: int
    max_in_team: int
    hidden: bool


class GameRoleCreate(BaseModel):
    name: str
    role_set_id: UUID
    min_in_team: int
    max_in_team: int
    icon_id: UUID | None = None
    hidden: bool = False


class GameRoleUpdate(BaseModel):
    id: UUID
    name: str | None = None
    min_in_team: int | None = None
    max_in_team: int | None = None
    icon_id: UUID | None = None
    hidden: bool | None = None
