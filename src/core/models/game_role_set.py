from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .game_role import GameRole


class GameRoleSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    game_id: UUID


class GameRoleSetDetail(GameRoleSet):
    game_roles: list[GameRole] = []


class GameRoleSetCreate(BaseModel):
    name: str
    game_id: UUID


class GameRoleSetUpdate(BaseModel):
    id: UUID
    name: str | None = None
