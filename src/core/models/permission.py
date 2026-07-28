from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Permission(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str


class PermissionCreate(BaseModel):
    code: str
