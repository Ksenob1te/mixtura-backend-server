from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Restriction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str


class RestrictionCreate(BaseModel):
    code: str
