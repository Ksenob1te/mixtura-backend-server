import logging

from faststream.rabbit import RabbitRouter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.game_role import (
    GameRoleItemCreateRequest,
    GameRoleItemDeleteRequest,
    GameRoleItemResponse,
    GameRoleItemUpdateRequest,
    GameRoleSetResponse,
    GameRoleSetUpdateRequest,
    GlobalGameRoleCreateRequest,
    GlobalGameRoleDeleteRequest,
    GlobalGameRoleSetUpdateRequest,
    GlobalGameRoleUpdateRequest,
)
from src.dependency import GameRoleServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber("role_set.update")
async def update_role_set(
    data: GameRoleSetUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleSetResponse]:
    role_set = await game_role_service.update_role_set(
        data.access_data.server_id, data.role_set_id, data.name, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=GameRoleSetResponse.model_validate(role_set))


@router.subscriber("role_set.role.create")
async def create_role(
    data: GameRoleItemCreateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.create_role(
        data.access_data.server_id, data.role_set_id, data.name, data.min_in_team, data.max_in_team,
        data.icon_id, data.hidden, data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.role.update")
async def update_role(
    data: GameRoleItemUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.update_role(
        data.access_data.server_id, data.role_id, data.name, data.min_in_team, data.max_in_team,
        data.icon_id, data.hidden, data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.role.icon.delete")
async def delete_role_icon(
    data: GameRoleItemDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_role_icon(
        data.access_data.server_id, data.role_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("role_set.role.delete")
async def delete_role(
    data: GameRoleItemDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_role(
        data.access_data.server_id, data.role_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("role_set.global.update")
async def update_global_role_set(
    data: GlobalGameRoleSetUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleSetResponse]:
    role_set = await game_role_service.update_global_role_set(data.role_set_id, data.name)
    return ResponseMessage(status=200, message=GameRoleSetResponse.model_validate(role_set))


@router.subscriber("role_set.global.role.create")
async def create_global_role(
    data: GlobalGameRoleCreateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.create_global_role(
        data.role_set_id, data.name, data.min_in_team, data.max_in_team, data.icon_id, data.hidden
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.global.role.update")
async def update_global_role(
    data: GlobalGameRoleUpdateRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[GameRoleItemResponse]:
    role = await game_role_service.update_global_role(
        data.role_id, data.name, data.min_in_team, data.max_in_team, data.icon_id, data.hidden
    )
    return ResponseMessage(status=200, message=GameRoleItemResponse.model_validate(role))


@router.subscriber("role_set.global.role.icon.delete")
async def delete_global_role_icon(
    data: GlobalGameRoleDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_global_role_icon(data.role_id)
    return ResponseMessage(status=200, message=StatusResponse())


@router.subscriber("role_set.global.role.delete")
async def delete_global_role(
    data: GlobalGameRoleDeleteRequest, game_role_service: GameRoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await game_role_service.delete_global_role(data.role_id)
    return ResponseMessage(status=200, message=StatusResponse())
