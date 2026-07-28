from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .rating import Rating


class RatingSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    min_rating: int
    max_rating: int
    game_id: UUID


class RatingSetDetail(RatingSet):
    ratings: list[Rating] = []


class RatingSetCreate(BaseModel):
    name: str
    min_rating: int
    max_rating: int
    game_id: UUID


class RatingSetUpdate(BaseModel):
    id: UUID
    name: str | None = None
    min_rating: int | None = None
    max_rating: int | None = None
