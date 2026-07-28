from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Custom(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    member_id: UUID
    creator_id: UUID | None = None


class CustomCreate(BaseModel):
    member_id: UUID
    creator_id: UUID | None = None
