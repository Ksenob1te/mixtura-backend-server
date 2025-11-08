from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List
from datetime import datetime


class ProviderModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    client_id: Optional[str]
    client_username: Optional[str]


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: Optional[str]
    email: Optional[str]
    registration_date: datetime
    providers: List[ProviderModel]
