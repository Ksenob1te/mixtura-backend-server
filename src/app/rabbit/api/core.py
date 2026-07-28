import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.server import (
    GetPublicServersRequest,
    GetUserServersRequest,
    ServerCreateRequest,
    ServerDeleteRequest,
    ServerGetRequest,
    ServerListResponse,
    ServerUpdateRequest,
)
from src.dependency import CoreServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.public_server_list")
async def get_public_servers(
    data: GetPublicServersRequest, core_service: CoreServiceDependency
) -> ResponseMessage[list[ServerListResponse]]:
    servers = await core_service.list_servers(
        data.pagination.page, data.name_filter, data.pagination.page_size
    )
    ta = TypeAdapter(list[ServerListResponse])
    return ResponseMessage(status=200, message=ta.validate_python(servers))


@router.subscriber(queue="server.user_server_list")
async def get_user_servers(
    data: GetUserServersRequest, core_service: CoreServiceDependency
) -> ResponseMessage[list[ServerListResponse]]:
    servers = await core_service.list_user_servers(
        data.user_id, data.pagination.page, data.name_filter, data.pagination.page_size
    )
    ta = TypeAdapter(list[ServerListResponse])
    return ResponseMessage(status=200, message=ta.validate_python(servers))


@router.subscriber(queue="server.create")
async def create_server(
    data: ServerCreateRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerListResponse]:
    server = await core_service.create_server(
        data.name, data.user_id, data.user_name, data.description, data.public,
    )
    return ResponseMessage(status=200, message=ServerListResponse.model_validate(server))


@router.subscriber(queue="server.get_info")
async def get_server(
    data: ServerGetRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerListResponse]:
    server = await core_service.get_server(data.access_data.server_id)
    return ResponseMessage(
        status=200, message=ServerListResponse.model_validate(server)
    )


@router.subscriber(queue="server.update")
async def update_server(
    data: ServerUpdateRequest, core_service: CoreServiceDependency
) -> ResponseMessage[ServerListResponse]:
    server = await core_service.update_server(
        data.access_data.server_id,
        data.name,
        data.description,
        data.public,
        data.banner_id,
        data.icon_id,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=ServerListResponse.model_validate(server))


@router.subscriber(queue="server.banner.delete")
async def delete_banner(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    await core_service.delete_server_banner(
        data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="server.icon.delete")
async def delete_icon(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    await core_service.delete_server_icon(
        data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber(queue="server.delete")
async def delete_server(
    data: ServerDeleteRequest, core_service: CoreServiceDependency
) -> ResponseMessage[StatusResponse]:
    await core_service.delete_server(
        data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
