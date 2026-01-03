import logging
from faststream.rabbit import RabbitRouter

from src.domain.models.response import ResponseMessage, StatusResponse
from ..models.roles.request import (
    CreateServerRoleRequest,
    DeleteServerRoleRequest,
    ListServerRolesRequest,
    UpdateServerRoleRequest,
)
from ..models.roles.response import ServerRoleResponse


router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.global.permissions")
async def get_global_permissions() -> ResponseMessage[list[str]]: ...


@router.subscriber(queue="server.role.list")
def list_roles(
    data: ListServerRolesRequest,
) -> ResponseMessage[list[ServerRoleResponse]]: ...


@router.subscriber(queue="server.role.create")
def create_role(
    data: CreateServerRoleRequest,
) -> ResponseMessage[ServerRoleResponse]: ...


@router.subscriber(queue="server.role.update")
def update_role(
    data: UpdateServerRoleRequest,
) -> ResponseMessage[ServerRoleResponse]: ...


@router.subscriber(queue="server.role.delete")
def delete_role(data: DeleteServerRoleRequest) -> ResponseMessage[StatusResponse]: ...
