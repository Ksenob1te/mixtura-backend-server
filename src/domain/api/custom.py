import logging
from faststream.rabbit import RabbitRouter

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
def get_customs_by_member(
    data: GetCustomsRequest,
) -> ResponseMessage[CustomResponse]: ...


@router.subscriber(queue="custom.create")
def create_custom(data: CreateCustomRequest) -> ResponseMessage[CustomResponse]: ...


@router.subscriber(queue="custom.delete")
def delete_custom(data: DeleteCustomRequest) -> ResponseMessage[StatusResponse]: ...


@router.subscriber(queue="custom.rating.set")
def update_custom(
    data: UpdateGameRoleRatingRequest,
) -> ResponseMessage[CustomResponse]: ...
