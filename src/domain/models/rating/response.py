from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RatingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    icon_id: UUID
    threshold: int

class RatingSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    min_rating: int
    max_rating: int
    is_global: bool
    ratings: list[RatingItemResponse] = []