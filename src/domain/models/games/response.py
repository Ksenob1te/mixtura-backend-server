from uuid import UUID
from pydantic import BaseModel, ConfigDict


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    icon_url: str
    banner_url: str