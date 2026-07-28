from uuid import UUID

from pydantic import BaseModel


class MemberListCommand(BaseModel):
    server_id: UUID
    page: int | None = None
    nickname_filter: str = ""
    page_size: int = 50


class MemberJoinCommand(BaseModel):
    server_id: UUID
    user_id: UUID
    nickname: str
    restriction_mask: int = 0


class MemberUpdateCommand(BaseModel):
    server_id: UUID
    issuer_id: UUID
    permission_mask: int
    restriction_mask: int
    member_id: UUID
    name: str | None = None
    server_role_id: UUID | None = None


class MemberKickCommand(BaseModel):
    issuer_id: UUID
    server_id: UUID
    member_id: UUID
    permission_mask: int
