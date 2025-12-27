import logging
from faststream.rabbit import RabbitRouter

from src.domain.models.core.request import (
    GetUseServersRequest,
    ServerCreateRequest,
    ServerDeleteRequest,
    ServerGetRequest,
    ServerUpdateRequest,
)
from src.domain.models.core.response import ServerDetailResponse, ServerListResponse
from src.domain.models.member.response import RestrictionResponse
from src.domain.models.rating.response import RatingSetResponse
from src.domain.models.response import ResponseMessage, StatusResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.global.rating_sets")
async def get_global_rating_templates() -> ResponseMessage[list[RatingSetResponse]]: ...


@router.subscriber(queue="server.global.permissions")
async def get_global_permissions() -> ResponseMessage[list[str]]: ...


@router.subscriber(queue="server.global.restrictions")
async def get_global_restrictions() -> ResponseMessage[list[RestrictionResponse]]: ...


@router.subscriber(queue="server.public_server_list")
async def get_public_servers() -> ResponseMessage[list[ServerListResponse]]: ...


@router.subscriber(queue="server.user_server_list")
async def get_user_servers(
    data: GetUseServersRequest,
) -> ResponseMessage[list[ServerListResponse]]: ...


@router.subscriber(queue="server.create")
async def create_server(
    data: ServerCreateRequest,
) -> ResponseMessage[ServerDetailResponse]: ...


@router.subscriber(queue="server.get_info")
async def get_server(
    data: ServerGetRequest,
) -> ResponseMessage[ServerDetailResponse]: ...


@router.subscriber(queue="server.update")
async def update_server(
    data: ServerUpdateRequest,
) -> ResponseMessage[ServerDetailResponse]: ...


@router.subscriber(queue="server.delete")
async def delete_server(
    data: ServerDeleteRequest,
) -> ResponseMessage[StatusResponse]: ...
