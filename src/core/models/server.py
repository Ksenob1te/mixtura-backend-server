from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Server(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    owner_id: UUID
    description: str
    public: bool
    icon_id: UUID | None = None
    banner_id: UUID | None = None
    created_at: datetime


class ServerCreate(BaseModel):
    name: str
    owner_id: UUID
    description: str
    public: bool


class ServerUpdate(BaseModel):
    id: UUID
    name: str | None = None
    description: str | None = None
    public: bool | None = None
    icon_id: UUID | None = None
    banner_id: UUID | None = None
