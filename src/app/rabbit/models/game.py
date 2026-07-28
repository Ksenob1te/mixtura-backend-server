from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app.rabbit.models.base import AccessDataRequest


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


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    icon_id: UUID
    banner_id: UUID
