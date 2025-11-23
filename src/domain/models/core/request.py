from uuid import UUID
from pydantic import BaseModel, Field

class ServerCreateRequest(BaseModel):
    name: str = Field(..., max_length=128)
    description: str = Field(default="")
    public: bool
    
    rating_set_id: UUID | None = None
    role_set_id: UUID | None = None

    game_ids: list[UUID] = [] 

class ServerUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    public: bool | None = None