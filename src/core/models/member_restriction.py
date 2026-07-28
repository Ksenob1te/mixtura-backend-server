from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MemberRestriction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member_id: UUID
    restriction_id: UUID
    reason: str
    expiration_date: datetime
    creator_id: UUID


class MemberRestrictionCreate(BaseModel):
    member_id: UUID
    restriction_id: UUID
    reason: str
    expiration_date: datetime
    creator_id: UUID
