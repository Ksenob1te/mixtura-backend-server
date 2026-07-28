import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.game_role import (
    GameRoleItemCreateRequest,
    GameRoleItemDeleteRequest,
    GameRoleItemResponse,
    GameRoleItemUpdateRequest,
    GameRoleSetResponse,
    GameRoleSetUpdateRequest,
    GetServerGameRoleSetsRequest,
)
from src.dependency import CoreServiceDependency, GameRoleServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="role_set.get_global")
async def get_global_role_templates(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[GameRoleSetResponse]]:
    role_sets = await core_service.get_global_role_templates()
    ta = TypeAdapter(list[GameRoleSetResponse])
    return ResponseMessage(status=200, message=ta.validate_python(role_sets))


@router.subscriber("role_set.get_by_server")
async def get_role_set(
    data: GetServerGameRoleSetsRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleSetResponse]:
    role_set = await game_role_service.get_role_set_for_server(data.access_data.server_id)
    return ResponseMessage(status=200, message=GameRoleSetResponse.model_validate(role_set))


@router.subscriber("role_set.update")
async def update_role_set(
    data: GameRoleSetUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleSetResponse]:
    role_set = await game_role_service.update_role_set(
        data.role_set_id, data.access_data.server_id, data.name, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=GameRoleSetResponse.model_validate(role_set))


@router.subscriber("role_set.role.create")
async def create_role(
    data: GameRoleItemCreateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.create_role(
        data.role_set_id, data.access_data.server_id, data.name, data.min_in_team, data.max_in_team,
        data.icon_id, data.hidden, data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.role.update")
async def update_role(
    data: GameRoleItemUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.update_role(
        data.role_id, data.access_data.server_id, data.name, data.min_in_team, data.max_in_team,
        data.icon_id, data.hidden, data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.role.icon.delete")
async def delete_role_icon(
    data: GameRoleItemDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_role_icon(
        data.role_id, data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("role_set.role.delete")
async def delete_role(
    data: GameRoleItemDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_role(
        data.role_id, data.access_data.server_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
