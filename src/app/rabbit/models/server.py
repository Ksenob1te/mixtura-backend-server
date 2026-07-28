from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.rabbit.models.base import AccessDataRequest, PaginationRequest
from src.app.rabbit.models.game import GameResponse
from src.app.rabbit.models.game_role import GameRoleSetResponse
from src.app.rabbit.models.rating import RatingSetResponse


class GetUserServersRequest(BaseModel):
    user_id: UUID
    pagination: PaginationRequest
    name_filter: str = ""


class GetPublicServersRequest(BaseModel):
    pagination: PaginationRequest
    name_filter: str = ""


class ServerGetRequest(BaseModel):
    access_data: AccessDataRequest


class ServerDeleteRequest(BaseModel):
    access_data: AccessDataRequest


class ServerCreateRequest(BaseModel):
    user_id: UUID
    user_name: str
    name: str = Field(..., max_length=128)
    description: str = Field(default="")
    public: bool
    rating_set_id: UUID | None = None
    role_set_id: UUID | None = None


class ServerUpdateRequest(BaseModel):
    access_data: AccessDataRequest
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    public: bool | None = None
    banner_id: UUID | None = None
    icon_id: UUID | None = None


class ServerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str
    icon_id: None | UUID = None
    banner_id: None | UUID = None
    owner_id: UUID
    public: bool
    created_at: datetime


class ServerDetailResponse(ServerListResponse):
    rating_set: RatingSetResponse | None = None
    role_set: GameRoleSetResponse | None = None
    games: list[GameResponse] = []
