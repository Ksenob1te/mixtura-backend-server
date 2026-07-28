from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RatingSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    min_rating: int
    max_rating: int
    is_global: bool
    server_id: UUID | None = None


class RatingSetCreate(BaseModel):
    name: str
    min_rating: int
    max_rating: int
    is_global: bool = False
    server_id: UUID | None = None


class RatingSetUpdate(BaseModel):
    id: UUID
    name: str | None = None
    min_rating: int | None = None
    max_rating: int | None = None
