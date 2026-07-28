import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.rating import (
    GetServerRatingSetsRequest,
    RatingItemCreateRequest,
    RatingItemDeleteRequest,
    RatingItemResponse,
    RatingItemUpdateRequest,
    RatingSetResponse,
    RatingSetUpdateRequest,
)
from src.dependency import CoreServiceDependency, RatingServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="rating_set.get_global")
async def get_global_rating_templates(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[RatingSetResponse]]:
    rating_sets = await core_service.get_global_rating_templates()
    ta = TypeAdapter(list[RatingSetResponse])
    return ResponseMessage(status=200, message=ta.validate_python(rating_sets))


@router.subscriber("rating_set.get_by_server")
async def get_rating_set(
    data: GetServerRatingSetsRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingSetResponse]:
    rating_set = await rating_service.get_rating_set(data.access_data.server_id)
    return ResponseMessage(status=200, message=RatingSetResponse.model_validate(rating_set))


@router.subscriber("rating_set.update")
async def update_rating_set(
    data: RatingSetUpdateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingSetResponse]:
    rating_set = await rating_service.update_rating_set(
        data.access_data.server_id, data.rating_set_id, data.name, data.min_rating, data.max_rating,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=RatingSetResponse.model_validate(rating_set))


@router.subscriber("rating_set.rating.create")
async def create_rating(
    data: RatingItemCreateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingItemResponse]:
    rating = await rating_service.create_rating(
        data.access_data.server_id, data.rating_set_id, data.threshold, data.icon_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=RatingItemResponse.model_validate(rating))


@router.subscriber("rating_set.rating.update")
async def update_rating(
    data: RatingItemUpdateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingItemResponse]:
    rating = await rating_service.update_rating(
        data.access_data.server_id, data.rating_item_id, data.threshold, data.icon_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=RatingItemResponse.model_validate(rating))


@router.subscriber("rating_set.rating.delete")
async def delete_rating(
    data: RatingItemDeleteRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[StatusResponse]:
    await rating_service.delete_rating(
        data.access_data.server_id, data.rating_item_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
