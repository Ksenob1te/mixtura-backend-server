import logging

from faststream.rabbit import RabbitRouter
from pydantic import TypeAdapter

from src.app.rabbit.models.base import ResponseMessage, StatusResponse
from src.app.rabbit.models.role import (
    CreateServerRoleRequest,
    DeleteServerRoleRequest,
    ListServerRolesRequest,
    PermissionResponse,
    ServerRoleResponse,
    UpdateServerRolePermissionsRequest,
    UpdateServerRoleRequest,
)
from src.dependency import CoreServiceDependency, RoleServiceDependency

router = RabbitRouter()
logger = logging.getLogger(__name__)


@router.subscriber(queue="server.global.permissions")
async def get_global_permissions(
    core_service: CoreServiceDependency,
) -> ResponseMessage[list[PermissionResponse]]:
    permissions = await core_service.get_global_permissions()
    ta = TypeAdapter(list[PermissionResponse])
    return ResponseMessage(status=200, message=ta.validate_python(permissions))


@router.subscriber(queue="server.role.list")
async def list_roles(
    data: ListServerRolesRequest, role_service: RoleServiceDependency
) -> ResponseMessage[list[ServerRoleResponse]]:
    roles = await role_service.list_roles(data.access_data.server_id)
    ta = TypeAdapter(list[ServerRoleResponse])
    return ResponseMessage(status=200, message=ta.validate_python(roles))


@router.subscriber(queue="server.role.create")
async def create_role(
    data: CreateServerRoleRequest, role_service: RoleServiceDependency
) -> ResponseMessage[ServerRoleResponse]:
    role = await role_service.create_role(
        data.access_data.server_id,
        data.name,
        data.position,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=ServerRoleResponse.model_validate(role))


@router.subscriber(queue="server.role.update")
async def update_role(
    data: UpdateServerRoleRequest, role_service: RoleServiceDependency
) -> ResponseMessage[ServerRoleResponse]:
    role = await role_service.update_role(
        data.access_data.server_id,
        data.role_id,
        data.name,
        data.position,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=ServerRoleResponse.model_validate(role))


@router.subscriber(queue="server.role.permissions.update")
async def update_role_permission(
    data: UpdateServerRolePermissionsRequest, role_service: RoleServiceDependency
) -> ResponseMessage[ServerRoleResponse]:
    role = await role_service.set_permissions(
        data.access_data.server_id,
        data.role_id,
        data.target_permissions_ids,
        data.access_data.permission_mask,
    )
    return ResponseMessage(status=200, message=ServerRoleResponse.model_validate(role))


@router.subscriber(queue="server.role.delete")
async def delete_role(
    data: DeleteServerRoleRequest, role_service: RoleServiceDependency
) -> ResponseMessage[StatusResponse]:
    await role_service.delete_role(
        data.access_data.server_id, data.role_id, data.access_data.permission_mask
    )
    return ResponseMessage(status=200, message=StatusResponse())
