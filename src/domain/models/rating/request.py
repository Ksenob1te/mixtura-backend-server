from uuid import UUID
from pydantic import BaseModel, Field

from ..request import AccessDataRequest


class GetServerRatingSetsRequest(BaseModel):
    access_data: AccessDataRequest


class RatingSetUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    rating_set_id: UUID

    name: str | None = Field(None, max_length=32)
    min_rating: int | None = None
    max_rating: int | None = None


class RatingItemCreateRequest(BaseModel):
    access_data: AccessDataRequest

    rating_set_id: UUID

    icon_id: UUID | None
    threshold: int


class RatingItemUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    rating_item_id: UUID
    threshold: int | None = None
    icon_id: UUID | None = None


class RatingItemDeleteRequest(BaseModel):
    access_data: AccessDataRequest

    rating_item_id: UUID
