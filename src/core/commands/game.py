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


class GlobalGameCreateCommand(BaseModel):
    name: str
    min_rating: int
    max_rating: int
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GlobalGameUpdateCommand(BaseModel):
    game_id: UUID
    name: str | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GlobalGameDeleteCommand(BaseModel):
    game_id: UUID


class LocalGameCreateCommand(BaseModel):
    server_id: UUID
    name: str
    min_rating: int
    max_rating: int
    icon_id: UUID | None = None
    banner_id: UUID | None = None
    permission_mask: int = 0


class LocalGameCopyCommand(BaseModel):
    server_id: UUID
    game_id: UUID
    permission_mask: int = 0


class LocalGameUpdateCommand(BaseModel):
    server_id: UUID
    game_id: UUID
    name: str | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None
    permission_mask: int = 0


class LocalGameDeleteCommand(BaseModel):
    server_id: UUID
    game_id: UUID
    permission_mask: int = 0
