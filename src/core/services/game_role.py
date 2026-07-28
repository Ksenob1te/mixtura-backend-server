from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.game_role import GameRoleRepositoryProtocol
from src.core.interfaces.repo.game_role_set import GameRoleSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.game_role import GameRole, GameRoleCreate, GameRoleUpdate
from src.core.models.game_role_set import GameRoleSet, GameRoleSetUpdate
from src.infra.postgre.static import PERMISSION


class GameRoleService:
    def __init__(
            self,
            server_repo: ServerRepositoryProtocol,
            role_set_repo: GameRoleSetRepositoryProtocol,
            role_repo: GameRoleRepositoryProtocol,
    ) -> None:
        self.server_repo = server_repo
        self.role_set_repo = role_set_repo
        self.role_repo = role_repo

    async def get_role_set_for_server(self, server_id: UUID) -> GameRoleSet:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        role_set = await self.role_set_repo.get_by_server_id(server_id)
        if role_set is None:
            raise InternalLogicException("Role set not found for server")
        return role_set

    async def update_role_set(
            self, role_set_id: UUID, server_id: UUID, name: str | None = None, permission_mask: int = 0
    ) -> GameRoleSet:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        server_field = await self.server_repo.get(server_id)
        if server_field is None:
            raise NotFoundException("Server not found")

        role_set_field = await self.role_set_repo.get_by_server_id(server_id)
        if role_set_field is None or role_set_field.id != role_set_id:
            raise NotFoundException("Role set not found for server")
        if name is not None and name != role_set_field.name:
            role_set_field = await self.role_set_repo.update(GameRoleSetUpdate(id=role_set_id, name=name))
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
        server_field = await self.server_repo.get(server_id)
        if server_field is None:
            raise NotFoundException("Server not found")
        role_set_field = await self.role_set_repo.get_by_server_id(server_id)
        if role_set_field is None or role_set_field.id != role_set_id:
            raise NotFoundException("Role set not found for server")
        try:
            role = await self.role_repo.create(
                GameRoleCreate(
                    name=name,
                    role_set_id=role_set_id,
                    min_in_team=min_in_team,
                    max_in_team=max_in_team,
                    icon_id=icon_id,
                    hidden=hidden,
                )
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role

    async def _check_role_belongs_to_server(self, role_id: UUID, server_id: UUID) -> GameRole:
        server_field = await self.server_repo.get(server_id)
        role_field = await self.role_repo.get(role_id)
        if server_field is None:
            raise NotFoundException("Server not found for server")
        role_set_field = await self.role_set_repo.get_by_server_id(server_id)
        if not role_field or not role_set_field or role_set_field.id != role_field.role_set_id:
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

        update_data: dict = {}
        if name is not None and name != role_field.name:
            update_data["name"] = name
        if hidden is not None and hidden != role_field.hidden:
            update_data["hidden"] = hidden
        if min_in_team is not None:
            update_data["min_in_team"] = min_in_team
        if max_in_team is not None:
            update_data["max_in_team"] = max_in_team
        if icon_id is not None:
            update_data["icon_id"] = icon_id

        if update_data:
            role_field = await self.role_repo.update(GameRoleUpdate(id=role_id, **update_data))
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
        role_field = await self.role_repo.update(GameRoleUpdate(id=role_id, icon_id=None))
        return role_field
