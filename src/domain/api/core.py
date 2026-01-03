import logging
from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from ...dependency import CoreServiceDependency
from src.domain.models.core.request import (
    GetUseServersRequest,
    ServerCreateRequest,
    ServerDeleteRequest,
    ServerGetRequest,
    ServerUpdateRequest,
)
from src.domain.models.core.response import ServerDetailResponse, ServerListResponse
from src.domain.models.response import ResponseMessage, StatusResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.public_server_list")
async def get_public_servers(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[ServerListResponse]]:
    servers = await core_service.list_servers()
    ta = TypeAdapter(list[ServerListResponse])
    return ResponseMessage(status=200, message=ta.validate_python(servers))


@router.subscriber(queue="server.user_server_list")
async def get_user_servers(
    data: GetUseServersRequest, core_service: CoreServiceDependency
) -> ResponseMessage[list[ServerListResponse]]:
    servers = await core_service.list_user_servers(data.user_id)
    ta = TypeAdapter(list[ServerListResponse])
    return ResponseMessage(status=200, message=ta.validate_python(servers))


@router.subscriber(queue="server.create")
async def create_server(
    data: ServerCreateRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerDetailResponse]:
    server = await core_service.create_server(
        data.user_id, data.name, data.description, data.public
    )
    return ResponseMessage(
        status=200, message=ServerDetailResponse.model_validate(server)
    )


@router.subscriber(queue="server.get_info")
async def get_server(
    data: ServerGetRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerDetailResponse]:
    server = await core_service.get_server(data.access_data.server_id)
    return ResponseMessage(
        status=200, message=ServerDetailResponse.model_validate(server)
    )


@router.subscriber(queue="server.update")
async def update_server(
    data: ServerUpdateRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerDetailResponse]:
    server = await core_service.update_server(
        data.access_data.server_id,
        data.name,
        data.description,
        data.public,
        data.banner_id,
        data.icon_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(
        status=200, message=ServerDetailResponse.model_validate(server)
    )


@router.subscriber(queue="server.banner.delete")
async def delete_banner(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    # TODO: delete banner
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="server.icon.delete")
async def delete_icon(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    # TODO: delete icon
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="server.delete")
async def delete_server(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    await core_service.delete_server(
        data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
