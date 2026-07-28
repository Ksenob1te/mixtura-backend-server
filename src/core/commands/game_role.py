from uuid import UUID

from pydantic import BaseModel


class GameRoleCreateCommand(BaseModel):
    role_set_id: UUID
    server_id: UUID
    name: str
    min_in_team: int
    max_in_team: int
    icon_id: UUID | None = None
    hidden: bool = False
    permission_mask: int = 0


class GameRoleUpdateCommand(BaseModel):
    role_id: UUID
    server_id: UUID
    name: str | None = None
    min_in_team: int | None = None
    max_in_team: int | None = None
    icon_id: UUID | None = None
    hidden: bool | None = None
    permission_mask: int = 0
