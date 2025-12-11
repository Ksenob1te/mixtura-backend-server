from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import ForbiddenException, InternalLogicException, NotFoundException
from src.infra.postgre.models import ServerRole
from src.infra.postgre.repo import ServerRepository, ServerRoleRepository, MemberRepository
from src.infra.postgre.static import PERMISSION


class RoleService:
    def __init__(
            self,
            server_repo: ServerRepository,
            role_repo: ServerRoleRepository,
            member_repo: MemberRepository,
    ) -> None:
        self.server_repo = server_repo
        self.role_repo = role_repo
        self.member_repo = member_repo

    async def list_roles(self, server_id: UUID) -> list[ServerRole]:
        server = await self.server_repo.get_by_id(server_id)
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
            role = await self.role_repo.create(server_id=server_id, name=name, position=position)
        except IntegrityError:
            raise InternalLogicException("Failed to create role due to integrity error")
        if role is None:
            raise InternalLogicException("Failed to create role")
        return role

    async def update_role(
            self,
            role_id: UUID,
            name: str | None = None,
            position: int | None = None,
            permission_mask: int = 0,
    ) -> ServerRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to edit role")
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundException("Role not found")
        if name is not None and name != role.name:
            role = await self.role_repo.set_name(role, name)
        if position is not None:
            role = await self.role_repo.set_position(role, position)
        return role

    async def delete_role(
            self,
            role_id: UUID,
            permission_mask: int = 0,
    ) -> None:
        # TODO: test here if deleting role from server, that has assigned user to it - role set to None for this user
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ROLES):
            raise ForbiddenException("Unable to delete role")
        try:
            await self.role_repo.delete(role_id)
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - role not found
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise NotFoundException("Role not found")
            raise InternalLogicException("Failed to delete role")