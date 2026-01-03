from uuid import UUID

from pydantic import BaseModel

from ..request import AccessDataRequest


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
