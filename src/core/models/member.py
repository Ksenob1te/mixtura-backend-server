from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Member(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    server_id: UUID
    user_id: UUID | None
    nickname: str
    server_role_id: UUID | None
    active: bool
    joined_at: datetime


class MemberCreate(BaseModel):
    server_id: UUID
    user_id: UUID | None
    nickname: str
    server_role_id: UUID | None = None


class MemberUpdate(BaseModel):
    id: UUID
    nickname: str | None = None
    server_role_id: UUID | None = None
    user_id: UUID | None = None
    active: bool | None = None
