import logging
from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from ...dependency import MemberCustomServiceDependency

from ..models.custom.response import CustomResponse

from ..models.response import ResponseMessage, StatusResponse

from ..models.custom.request import (
    CreateCustomRequest,
    DeleteCustomRequest,
    GetCustomsRequest,
    UpdateGameRoleRatingRequest,
)


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="custom.get_by_member")
async def get_customs_by_member(
    data: GetCustomsRequest, custom_service: MemberCustomServiceDependency
) -> ResponseMessage[list[CustomResponse]]:
    customs = await custom_service.list_customs(
        data.access_data.server_id, data.target_member_id
    )
    ta = TypeAdapter(list[CustomResponse])
    return ResponseMessage(status=200, message=ta.validate_python(customs))


@router.subscriber(queue="custom.create")
async def create_custom(
    data: CreateCustomRequest, custom_service: MemberCustomServiceDependency
) -> ResponseMessage[CustomResponse]:
    custom = await custom_service.create_custom(
        data.access_data.member_id,
        data.access_data.server_id,
        data.target_member_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=CustomResponse.model_validate(custom))


@router.subscriber(queue="custom.delete")
async def delete_custom(
    data: DeleteCustomRequest, custom_service: MemberCustomServiceDependency
) -> ResponseMessage[StatusResponse]:
    await custom_service.delete_custom(
        data.access_data.member_id,
        data.custom_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="custom.rating.set")
async def update_custom(
    data: UpdateGameRoleRatingRequest, custom_service: MemberCustomServiceDependency
) -> ResponseMessage[CustomResponse]:
    custom = await custom_service.set_rating_value(
        data.access_data.member_id,
        data.access_data.server_id,
        data.custom_id,
        data.game_role_id,
        data.rating,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=CustomResponse.model_validate(custom))
