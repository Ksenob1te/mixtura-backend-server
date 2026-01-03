from uuid import UUID
from pydantic import BaseModel, Field

from ..request import AccessDataRequest


class GetServerGameRoleSetsRequest(BaseModel):
    access_data: AccessDataRequest


class GameRoleSetUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    role_set_id: UUID
    name: str | None = Field(None, max_length=32)


class GameRoleItemCreateRequest(BaseModel):
    access_data: AccessDataRequest

    role_set_id: UUID

    role_id: UUID
    name: str = Field(max_length=32)
    min_in_team: int
    max_in_team: int
    hidden: bool = False
    icon_id: UUID | None = None


class GameRoleItemUpdateRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID
    name: str | None = Field(None, max_length=32)
    min_in_team: int | None = None
    max_in_team: int | None = None
    hidden: bool | None = None
    icon_id: UUID | None = None


class GameRoleItemDeleteRequest(BaseModel):
    access_data: AccessDataRequest

    role_id: UUID
