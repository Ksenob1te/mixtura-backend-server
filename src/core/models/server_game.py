from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServerGame(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    server_id: UUID
    game_id: UUID
