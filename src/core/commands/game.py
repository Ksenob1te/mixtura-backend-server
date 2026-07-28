from uuid import UUID

from pydantic import BaseModel


class GameAddCommand(BaseModel):
    server_id: UUID
    game_ids: list[UUID]
    permission_mask: int = 0


class GameRemoveCommand(BaseModel):
    server_id: UUID
    game_id: UUID
    permission_mask: int = 0


class GameSetCommand(BaseModel):
    server_id: UUID
    game_ids: list[UUID]
    permission_mask: int = 0
