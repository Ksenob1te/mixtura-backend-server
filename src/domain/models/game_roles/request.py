from pydantic import BaseModel, ConfigDict, Field


class GameRoleItemUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=32)
    min_in_team: int | None = None
    max_in_team: int | None = None
    hidden: bool | None = None

class GameRoleItemCreateRequest(BaseModel):
    name: str = Field( max_length=32)
    min_in_team: int
    max_in_team: int
    hidden: bool = False

class GameRoleSetUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=32)