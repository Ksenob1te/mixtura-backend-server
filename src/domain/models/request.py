from uuid import UUID
from pydantic import BaseModel


class UserIncludedRequest(BaseModel):
    user_id: UUID

class MemberIncludedRequest(BaseModel):
    member_id: UUID
    permissions: int