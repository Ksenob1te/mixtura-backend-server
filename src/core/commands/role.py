from uuid import UUID

from pydantic import BaseModel


class RoleCreateCommand(BaseModel):
    server_id: UUID
    name: str
    position: int | None = None
    permission_mask: int = 0


class RoleUpdateCommand(BaseModel):
    server_id: UUID
    role_id: UUID
    name: str | None = None
    position: int | None = None
    permission_mask: int = 0
