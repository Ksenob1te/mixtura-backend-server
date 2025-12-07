from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class VirtualMemberCreateRequest(BaseModel):
    name: str


class MemberUpdateRequest(BaseModel):
    name: str | None = None
    server_role_id: UUID | None = None


class MigrationRequest(BaseModel):
    target_member_id: UUID


class MemberRestrictionCreateRequest(BaseModel):
    reason: str
    expiration_date: datetime
    restriction_id: UUID
