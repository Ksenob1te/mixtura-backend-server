from uuid import UUID

from pydantic import BaseModel


class GameAddRequest(BaseModel):
    ids: list[UUID]