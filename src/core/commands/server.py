from uuid import UUID

from pydantic import BaseModel


class ServerListCommand(BaseModel):
    page: int | None = None
    name_filter: str | None = None
    page_size: int = 50


class ServerCreateCommand(BaseModel):
    name: str
    owner_id: UUID
    username: str
    description: str
    public: bool
    rating_set_id: UUID | None = None
    role_set_id: UUID | None = None


class ServerUpdateCommand(BaseModel):
    server_id: UUID
    name: str | None = None
    description: str | None = None
    public: bool | None = None
    banner_id: UUID | None = None
    icon_id: UUID | None = None
    permission_mask: int = 0
