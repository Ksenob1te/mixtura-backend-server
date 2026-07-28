from uuid import UUID

from pydantic import BaseModel


class RatingSetUpdateCommand(BaseModel):
    server_id: UUID
    rating_set_id: UUID
    name: str | None = None
    min_rating: int | None = None
    max_rating: int | None = None
    permission_mask: int = 0


class RatingCreateCommand(BaseModel):
    server_id: UUID
    rating_set_id: UUID
    threshold: int
    icon_id: UUID | None = None
    permission_mask: int = 0


class RatingUpdateCommand(BaseModel):
    server_id: UUID
    rating_id: UUID
    threshold: int | None = None
    icon_id: UUID | None = None
    permission_mask: int = 0
