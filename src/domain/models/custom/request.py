from uuid import UUID
from pydantic import BaseModel

from ..request import AccessDataRequest


class GetCustomsRequest(BaseModel):
    access_data: AccessDataRequest

    target_member_id: UUID


class CreateCustomRequest(BaseModel):
    access_data: AccessDataRequest

    target_member_id: UUID


class GetCustomInfoRequest(BaseModel):
    access_data: AccessDataRequest

    custom_id: UUID


class DeleteCustomRequest(BaseModel):
    access_data: AccessDataRequest

    custom_id: UUID


class UpdateGameRoleRatingRequest(BaseModel):
    access_data: AccessDataRequest

    custom_id: UUID
    game_role_id: UUID
    rating: int
