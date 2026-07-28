from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .game_role_set import GameRoleSetDetail
from .rating_set import RatingSetDetail


class Game(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    server_id: UUID | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None

    @property
    def is_global(self) -> bool:
        return self.server_id is None


class GameDetail(Game):
    role_set: GameRoleSetDetail
    rating_set: RatingSetDetail


class GameCreate(BaseModel):
    name: str
    server_id: UUID | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GameUpdate(BaseModel):
    id: UUID
    name: str | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None
