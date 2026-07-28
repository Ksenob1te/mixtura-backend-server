from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.app.rabbit.models.base import AccessDataRequest
from src.app.rabbit.models.game_role import GameRoleItemResponse
from src.app.rabbit.models.member import ReducedMemberResponse


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


class CustomRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    game_role: GameRoleItemResponse
    rating: int


class CustomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    member: ReducedMemberResponse
    creator: ReducedMemberResponse
    custom_ratings: list[CustomRatingResponse]
