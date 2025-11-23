from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from src.domain.models.game_roles.response import GameRoleSetResponse
from src.domain.models.games.response import GameResponse
from src.domain.models.ratings.response import RatingSetResponse


class ServerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    icon_url: None | str = None
    banner_url: None | str = None
    owner_id: UUID
    public: bool
    created_at: datetime
    
    rating_set_id: None | UUID = None
    role_set_id:  None | UUID = None

class ServerDetailResponse(ServerListResponse):
    rating_set: Optional[RatingSetResponse] = None
    role_set: Optional[GameRoleSetResponse] = None
    
    games: list[GameResponse] = []