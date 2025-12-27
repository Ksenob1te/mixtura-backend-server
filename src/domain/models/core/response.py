from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from src.domain.models.game_roles.response import GameRoleSetResponse
from src.domain.models.games.response import GameResponse
from src.domain.models.rating.response import RatingSetResponse


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
    rating_set: Optional[RatingSetResponse] = None
    role_set: Optional[GameRoleSetResponse] = None
    
    games: list[GameResponse] = []