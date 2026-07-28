from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.permission import PermissionRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.interfaces.repo.server_role import ServerRoleRepositoryProtocol
from src.core.models.server_role import ServerRole, ServerRoleCreate, ServerRoleUpdate
from src.infra.postgre.static import PERMISSION


class RoleService:
    def __init__(
            self,
            server_repo: ServerRepositoryProtocol,
            role_repo: ServerRoleRepositoryProtocol,
            member_repo: MemberRepositoryProtocol,
            permission_repo: PermissionRepositoryProtocol,
    ) -> None:
        self.server_repo = server_repo
        self.role_repo = role_repo
        self.member_repo = member_repo
        self.permission_repo = permission_repo

    async def list_roles(self, server_id: UUID) -> list[ServerRole]:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        roles = await self.role_repo.list_for_server(server_id)
        return list(roles)

    async def create_role(
            self,
            server_id: UUID,
            name: str,
            position: int | None = None,
            permission_mask: int = 0,
    ) -> ServerRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to create role")
        if position is None:
            position = 0
        try:
            role = await self.role_repo.create(ServerRoleCreate(server_id=server_id, name=name, position=position))
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role

    async def update_role(
            self,
            server_id: UUID,
            role_id: UUID,
            name: str | None = None,
            position: int | None = None,
            permission_mask: int = 0,
    ) -> ServerRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to edit role")
        role = await self.role_repo.get(role_id)
        if role is None or role.server_id != server_id:
            raise NotFoundException("Role not found")

        update_data: dict = {}
        if name is not None and name != role.name:
            update_data["name"] = name
        if position is not None:
            update_data["position"] = position

        if update_data:
            role = await self.role_repo.update(ServerRoleUpdate(id=role_id, **update_data))
        return role

    async def add_permission(
            self,
            server_id: UUID,
            role_id: UUID,
            permission_id: UUID,
            permission_mask: int = 0,
    ) -> ServerRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to edit role")
        role_field = await self.role_repo.get(role_id)
        if role_field is None or role_field.server_id != server_id:
            raise NotFoundException("Role not found")
        try:
            await self.permission_repo.assign_to_role(permission_id, role_id)
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role_field

    async def remove_permission(
            self,
            server_id: UUID,
            role_id: UUID,
            permission_id: UUID,
            permission_mask: int = 0,
    ) -> ServerRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to edit role")
        role = await self.role_repo.get(role_id)
        if role is None or role.server_id != server_id:
            raise NotFoundException("Role not found")
        ok = await self.permission_repo.remove_from_role(permission_id, role_id)
        if not ok:
            raise NotFoundException("Permission not found in role")
        return role

    async def set_permissions(
            self,
            server_id: UUID,
            role_id: UUID,
            permission_ids: list[UUID],
            permission_mask: int = 0,
    ) -> ServerRole:
        role_field = await self.role_repo.get(role_id)
        if role_field is None or role_field.server_id != server_id:
            raise NotFoundException("Role not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to edit role")
        try:
            await self.permission_repo.bulk_set_for_role(permission_ids, role_id)
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role_field

    async def delete_role(
            self,
            server_id: UUID,
            role_id: UUID,
            permission_mask: int = 0,
    ) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to delete role")
        role_field = await self.role_repo.get(role_id)
        if role_field is None or role_field.server_id != server_id:
            raise NotFoundException("Role not found")
        ok = await self.role_repo.delete(role_id)
        if not ok:
            raise NotFoundException("Role not found")
