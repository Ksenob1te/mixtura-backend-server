from uuid import UUID
from pydantic import BaseModel, Field

from ..request import AccessDataRequest, PaginationRequest


class GetUserServersRequest(BaseModel):
    user_id: UUID
    pagination: PaginationRequest
    name_filter: str = ""

class GetPublicServersRequest(BaseModel):
    pagination: PaginationRequest
    name_filter: str = ""

class ServerGetRequest(BaseModel):
    access_data: AccessDataRequest


class ServerDeleteRequest(BaseModel):
    access_data: AccessDataRequest


class ServerCreateRequest(BaseModel):
    user_id: UUID
    user_name: str

    name: str = Field(..., max_length=128)
    description: str = Field(default="")
    public: bool
    rating_set_id: UUID | None = None
    role_set_id: UUID | None = None


class ServerUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    name: str | None = Field(None, max_length=128)
    description: str | None = None
    public: bool | None = None
    banner_id: UUID | None = None
    icon_id: UUID | None = None
