from uuid import UUID

from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.infra.postgre.models import GameRoleSet, GameRole
from src.infra.postgre.repo import (
    GameRoleSetRepository,
    GameRoleRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION
from src.infra.postgre import IntegrityForeignException, IntegrityUnknownException


class GameRoleService:
    def __init__(
            self,
            server_repo: ServerRepository,
            role_set_repo: GameRoleSetRepository,
            role_repo: GameRoleRepository,
    ) -> None:
        self.server_repo = server_repo
        self.role_set_repo = role_set_repo
        self.role_repo = role_repo

    async def get_role_set_for_server(self, server_id: UUID) -> GameRoleSet:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server.role_set

    async def update_role_set(
            self, role_set_id: UUID, server_id: UUID, name: str | None = None, permission_mask: int = 0
    ) -> GameRoleSet:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        server_field = await self.server_repo.get_by_id(server_id)
        if server_field is None:
            raise NotFoundException("Server not found")
        role_set_field = server_field.role_set

        if server_field.role_set_id != role_set_id or role_set_field is None:
            raise NotFoundException("Role set not found for server")
        if name is not None and name != role_set_field.name:
            role_set_field = await self.role_set_repo.set_name(role_set_field, name)
        return role_set_field

    async def create_role(
            self,
            role_set_id: UUID,
            server_id: UUID,
            name: str,
            min_in_team: int,
            max_in_team: int,
            icon_id: UUID | None = None,
            hidden: bool = False,
            permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        server_field = await self.server_repo.get_by_id(server_id)
        if server_field is None:
            raise NotFoundException("Server not found")
        role_set_field = server_field.role_set
        if server_field.role_set_id != role_set_id or not role_set_field:
            raise NotFoundException("Role set not found for server")
        try:
            role = await self.role_repo.create(
                name=name,
                role_set_id=role_set_id,
                min_in_team=min_in_team,
                max_in_team=max_in_team,
                icon_id=icon_id,
                hidden=hidden,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role

    async def _check_role_belongs_to_server(self, role_id: UUID, server_id: UUID) -> GameRole:
        server_field = await self.server_repo.get_by_id(server_id)
        role_field = await self.role_repo.get_by_id(role_id)
        if server_field is None:
            raise NotFoundException("Server not found for server")
        if not role_field or server_field.role_set_id != role_field.role_set_id:
            raise NotFoundException("Role not found for server")
        return role_field

    async def update_role(
            self,
            role_id: UUID,
            server_id: UUID,
            name: str | None = None,
            min_in_team: int | None = None,
            max_in_team: int | None = None,
            icon_id: UUID | None = None,
            hidden: bool | None = None,
            permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_field = await self._check_role_belongs_to_server(role_id, server_id)
        if name is not None and name != role_field.name:
            role_field = await self.role_repo.set_name(role_field, name)
        if hidden is not None and hidden != role_field.hidden:
            role_field = await self.role_repo.set_hidden(role_field, hidden)
        if min_in_team is not None:
            role_field = await self.role_repo.set_min(role_field, min_in_team)
        if max_in_team is not None:
            role_field = await self.role_repo.set_max(role_field, max_in_team)
        if icon_id is not None:
            role_field = await self.role_repo.set_icon(role_field, icon_id)
        return role_field

    async def delete_role(self, role_id: UUID, server_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to delete role")
        await self._check_role_belongs_to_server(role_id, server_id)
        deleted = await self.role_repo.delete(role_id)
        if not deleted:
            raise NotFoundException("Role not found")

    async def delete_role_icon(self, role_id: UUID, server_id: UUID, permission_mask: int = 0) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_field = await self._check_role_belongs_to_server(role_id, server_id)
        role_field = await self.role_repo.set_icon(role_field, None)
        return role_field
