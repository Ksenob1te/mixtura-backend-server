from uuid import UUID

from pydantic import BaseModel


class CustomCreateCommand(BaseModel):
    issuer_id: UUID
    server_id: UUID
    member_id: UUID
    permission_mask: int = 0


class CustomDeleteCommand(BaseModel):
    server_id: UUID
    custom_id: UUID
    permission_mask: int = 0


class CustomRatingSetCommand(BaseModel):
    issuer_id: UUID
    server_id: UUID
    custom_id: UUID
    game_role_id: UUID
    rating: int
    permission_mask: int = 0
