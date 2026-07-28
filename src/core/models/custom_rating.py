from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomRating(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    custom_id: UUID
    game_role_id: UUID
    rating: int


class CustomRatingCreate(BaseModel):
    custom_id: UUID
    game_role_id: UUID
    rating: int


class CustomRatingUpdate(BaseModel):
    id: UUID
    rating: int | None = None
