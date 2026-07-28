from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Game(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    icon_id: UUID
    banner_id: UUID


class GameCreate(BaseModel):
    name: str
    icon_id: UUID
    banner_id: UUID


class GameUpdate(BaseModel):
    id: UUID
    name: str | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None
