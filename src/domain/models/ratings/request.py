from pydantic import BaseModel, Field


class RatingItemUpdateRequest(BaseModel):
    threshold: int | None = None

class RatingItemCreateRequest(BaseModel):
    threshold: int

class RatingSetUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=32)
    min_rating: int | None = None
    max_rating: int | None = None