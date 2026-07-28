from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMessage(BaseModel, Generic[T]):  # noqa: UP046
    status: int
    message: T


class AccessDataRequest(BaseModel):
    member_id: UUID | None
    server_id: UUID
    permission_mask: int
    restriction_mask: int


class PaginationRequest(BaseModel):
    page: int | None = None
    page_size: int = 50


class ErrorResponse(BaseModel):
    message: str


class UpdateResponse(BaseModel):
    status: str = Field(default="ok")
    updated: bool = Field(default=True)


class StatusResponse(BaseModel):
    status: str = Field(default="ok")
