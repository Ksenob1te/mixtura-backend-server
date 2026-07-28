from uuid import UUID

from pydantic import BaseModel


class InviteCreateCommand(BaseModel):
    server_id: UUID
    use_limit: int
    inviter_id: UUID | None = None
    permission_mask: int = 0


class InviteRevokeCommand(BaseModel):
    server_id: UUID
    invite_id: UUID
    permission_mask: int = 0
