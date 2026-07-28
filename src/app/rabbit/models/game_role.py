from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.rabbit.models.base import AccessDataRequest


class GameRoleSetUpdateRequest(BaseModel):
    access_data: AccessDataRequest
    role_set_id: UUID
    name: str | None = Field(None, max_length=32)


class GameRoleItemCreateRequest(BaseModel):
    access_data: AccessDataRequest
    role_set_id: UUID
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


class GlobalGameRoleSetUpdateRequest(BaseModel):
    role_set_id: UUID
    name: str | None = Field(None, max_length=32)


class GlobalGameRoleCreateRequest(BaseModel):
    role_set_id: UUID
    name: str = Field(max_length=32)
    min_in_team: int
    max_in_team: int
    hidden: bool = False
    icon_id: UUID | None = None


class GlobalGameRoleUpdateRequest(BaseModel):
    role_id: UUID
    name: str | None = Field(None, max_length=32)
    min_in_team: int | None = None
    max_in_team: int | None = None
    hidden: bool | None = None
    icon_id: UUID | None = None


class GlobalGameRoleDeleteRequest(BaseModel):
    role_id: UUID


class GameRoleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    icon_id: UUID | None = None
    min_in_team: int
    max_in_team: int
    hidden: bool


class GameRoleSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    game_id: UUID
    game_roles: list[GameRoleItemResponse] = []
