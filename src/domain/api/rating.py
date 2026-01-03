import logging
from faststream.rabbit import RabbitRouter

from ..models.rating.request import (
    GetServerRatingSetsRequest,
    RatingItemCreateRequest,
    RatingItemDeleteRequest,
    RatingItemUpdateRequest,
    RatingSetUpdateRequest,
)

from ..models.response import ResponseMessage, StatusResponse

from ..models.rating.response import RatingItemResponse, RatingSetResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)



@router.subscriber(queue="rating_set.get_global")
async def get_global_rating_templates() -> ResponseMessage[list[RatingSetResponse]]: ...


@router.subscriber("rating_set.get_by_server")
def get_rating_set(
    data: GetServerRatingSetsRequest,
) -> ResponseMessage[RatingSetResponse]: ...


@router.subscriber("rating_set.update")
def update_rating_set(
    data: RatingSetUpdateRequest,
) -> ResponseMessage[RatingSetResponse]: ...


@router.subscriber("rating_set.rating.create")
def create_rating(
    data: RatingItemCreateRequest,
) -> ResponseMessage[RatingItemResponse]: ...


@router.subscriber("rating_set.rating.update")
def update_rating(
    data: RatingItemUpdateRequest,
) -> ResponseMessage[RatingItemResponse]: ...


@router.subscriber("rating_set.rating.delete")
def delete_rating(data: RatingItemDeleteRequest) -> ResponseMessage[StatusResponse]: ...
