from uuid import UUID
from pydantic import BaseModel, ConfigDict

from src.domain.models.game_roles.response import GameRoleItemResponse


class CustomRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_role: GameRoleItemResponse
    rating: int

class CustomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    custom_ratings: list[CustomRatingResponse]