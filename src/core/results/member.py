from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MemberResult(BaseModel):
    id: UUID
    server_id: UUID
    user_id: UUID | None
    nickname: str
    active: bool
    joined_at: datetime
