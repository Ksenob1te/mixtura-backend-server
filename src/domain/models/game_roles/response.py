from uuid import UUID
from pydantic import BaseModel, ConfigDict


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

    game_roles: list[GameRoleItemResponse] = []
