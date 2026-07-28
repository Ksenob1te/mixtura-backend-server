from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.rabbit.models.base import AccessDataRequest
from src.app.rabbit.models.game_role import GameRoleSetResponse
from src.app.rabbit.models.rating import RatingSetResponse


class GameAddRequest(BaseModel):
    access_data: AccessDataRequest
    game_ids: list[UUID]


class GameRemoveRequest(BaseModel):
    access_data: AccessDataRequest
    game_id: UUID


class GameSetRequest(BaseModel):
    access_data: AccessDataRequest
    game_ids: list[UUID]


class GetServerGameListRequest(BaseModel):
    access_data: AccessDataRequest


class GetOwnedGameListRequest(BaseModel):
    access_data: AccessDataRequest


class GlobalGameCreateRequest(BaseModel):
    name: str = Field(max_length=128)
    min_rating: int
    max_rating: int
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GlobalGameUpdateRequest(BaseModel):
    game_id: UUID
    name: str | None = Field(None, max_length=128)
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GlobalGameDeleteRequest(BaseModel):
    game_id: UUID


class LocalGameCreateRequest(BaseModel):
    access_data: AccessDataRequest
    name: str = Field(max_length=128)
    min_rating: int
    max_rating: int
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class LocalGameCopyRequest(BaseModel):
    access_data: AccessDataRequest
    game_id: UUID


class LocalGameUpdateRequest(BaseModel):
    access_data: AccessDataRequest
    game_id: UUID
    name: str | None = Field(None, max_length=128)
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class LocalGameDeleteRequest(BaseModel):
    access_data: AccessDataRequest
    game_id: UUID


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    server_id: UUID | None = None
    is_global: bool
    icon_id: UUID | None = None
    banner_id: UUID | None = None


class GameDetailResponse(GameResponse):
    role_set: GameRoleSetResponse
    rating_set: RatingSetResponse
