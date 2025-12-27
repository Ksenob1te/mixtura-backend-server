import logging
from faststream.rabbit import RabbitRouter

from ..models.game_roles.response import GameRoleItemResponse, GameRoleSetResponse

from ..models.game_roles.request import (
    GameRoleItemCreateRequest,
    GameRoleItemDeleteRequest,
    GameRoleItemUpdateRequest,
    GameRoleSetUpdateRequest,
    GetServerGameRoleSetsRequest,
)

from src.domain.models.response import ResponseMessage, StatusResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="role_set.get_global")
async def get_global_role_templates() -> ResponseMessage[list[GameRoleSetResponse]]: ...


@router.subscriber("role_set.get_by_server")
def get_role_set(
    data: GetServerGameRoleSetsRequest,
) -> ResponseMessage[GameRoleSetResponse]: ...


@router.subscriber("role_set.update")
def update_role_set(
    data: GameRoleSetUpdateRequest,
) -> ResponseMessage[GameRoleSetResponse]: ...


@router.subscriber("role_set.role.create")
def create_role(data: GameRoleItemCreateRequest) -> ResponseMessage[GameRoleItemResponse]: ...


@router.subscriber("role_set.role.update")
def update_role(data: GameRoleItemUpdateRequest) -> ResponseMessage[GameRoleItemResponse]: ...


@router.subscriber("role_set.role.delete")
def delete_role(data: GameRoleItemDeleteRequest) -> ResponseMessage[StatusResponse]: ...
