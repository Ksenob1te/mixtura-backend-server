from uuid import UUID
from pydantic import BaseModel, Field

from ..request import AccessDataRequest


class GetServerRatingSetsRequest(BaseModel):
    access_data: AccessDataRequest


class RatingSetUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    threshold: int | None = None
    icon_id: UUID | None = None


# TODO: misplace, icons
class RatingItemCreateRequest(BaseModel):
    access_data: AccessDataRequest

    threshold: int


class RatingItemUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    name: str | None = Field(None, max_length=32)
    min_rating: int | None = None
    max_rating: int | None = None


class RatingItemDeleteRequest(BaseModel):
    access_data: AccessDataRequest
