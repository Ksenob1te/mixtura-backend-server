import logging

from faststream.rabbit import RabbitRouter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.rating import (
    GlobalRatingCreateRequest,
    GlobalRatingDeleteRequest,
    GlobalRatingSetUpdateRequest,
    GlobalRatingUpdateRequest,
    RatingItemCreateRequest,
    RatingItemDeleteRequest,
    RatingItemResponse,
    RatingItemUpdateRequest,
    RatingSetResponse,
    RatingSetUpdateRequest,
)
from src.dependency import RatingServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


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


@router.subscriber("rating_set.rating.icon.delete")
async def delete_rating_icon(
    data: RatingItemDeleteRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[StatusResponse]:
    await rating_service.delete_rating_icon(
        data.access_data.server_id, data.rating_item_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("rating_set.rating.delete")
async def delete_rating(
    data: RatingItemDeleteRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[StatusResponse]:
    await rating_service.delete_rating(
        data.access_data.server_id, data.rating_item_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("rating_set.global.update")
async def update_global_rating_set(
    data: GlobalRatingSetUpdateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingSetResponse]:
    rating_set = await rating_service.update_global_rating_set(
        data.rating_set_id, data.name, data.min_rating, data.max_rating
    )
    return ResponseMessage(status=200, message=RatingSetResponse.model_validate(rating_set))


@router.subscriber("rating_set.global.rating.create")
async def create_global_rating(
    data: GlobalRatingCreateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingItemResponse]:
    rating = await rating_service.create_global_rating(data.rating_set_id, data.threshold, data.icon_id)
    return ResponseMessage(status=200, message=RatingItemResponse.model_validate(rating))


@router.subscriber("rating_set.global.rating.update")
async def update_global_rating(
    data: GlobalRatingUpdateRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[RatingItemResponse]:
    rating = await rating_service.update_global_rating(data.rating_item_id, data.threshold, data.icon_id)
    return ResponseMessage(status=200, message=RatingItemResponse.model_validate(rating))


@router.subscriber("rating_set.global.rating.icon.delete")
async def delete_global_rating_icon(
    data: GlobalRatingDeleteRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[StatusResponse]:
    await rating_service.delete_global_rating_icon(data.rating_item_id)
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("rating_set.global.rating.delete")
async def delete_global_rating(
    data: GlobalRatingDeleteRequest, rating_service: RatingServiceDependency
) -> ResponseMessage[StatusResponse]:
    await rating_service.delete_global_rating(data.rating_item_id)
    return ResponseMessage(status=200, message=StatusResponse())
