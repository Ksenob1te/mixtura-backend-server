from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Invite(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    server_id: UUID
    inviter_id: UUID | None = None
    key: str
    use_limit: int


class InviteCreate(BaseModel):
    server_id: UUID
    use_limit: int
    inviter_id: UUID | None = None
    key: str | None = None


class InviteUpdate(BaseModel):
    id: UUID
    use_limit: int | None = None
