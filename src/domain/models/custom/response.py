from uuid import UUID
from pydantic import BaseModel, ConfigDict

from ..game_roles.response import GameRoleItemResponse
from ..member.response import ReducedMemberResponse


class CustomRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    game_role: GameRoleItemResponse
    rating: int

class CustomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member: ReducedMemberResponse
    creator: ReducedMemberResponse
    custom_ratings: list[CustomRatingResponse]