from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Rating(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rating_set_id: UUID
    threshold: int
    icon_id: UUID | None = None


class RatingCreate(BaseModel):
    rating_set_id: UUID
    threshold: int
    icon_id: UUID | None = None


class RatingUpdate(BaseModel):
    id: UUID
    threshold: int | None = None
    icon_id: UUID | None = None
