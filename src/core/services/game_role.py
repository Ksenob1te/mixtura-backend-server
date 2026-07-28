from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.game import GameRepositoryProtocol
from src.core.interfaces.repo.game_role import GameRoleRepositoryProtocol
from src.core.interfaces.repo.game_role_set import GameRoleSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.game import Game
from src.core.models.game_role import GameRole, GameRoleCreate, GameRoleUpdate
from src.core.models.game_role_set import (
    GameRoleSet,
    GameRoleSetDetail,
    GameRoleSetUpdate,
)
from src.infra.postgre.static import PERMISSION


class GameRoleService:
    def __init__(
            self,
            server_repo: ServerRepositoryProtocol,
            game_repo: GameRepositoryProtocol,
            role_set_repo: GameRoleSetRepositoryProtocol,
            role_repo: GameRoleRepositoryProtocol,
    ) -> None:
        self.server_repo = server_repo
        self.game_repo = game_repo
        self.role_set_repo = role_set_repo
        self.role_repo = role_repo

    async def _set_and_game(self, role_set_id: UUID) -> tuple[GameRoleSet, Game]:
        role_set = await self.role_set_repo.get(role_set_id)
        if role_set is None:
            raise NotFoundException("Role set not found")
        game = await self.game_repo.get(role_set.game_id)
        if game is None:
            raise InternalLogicException("Game for role set not found")
        return role_set, game

    async def _require_local_set(self, server_id: UUID, role_set_id: UUID) -> GameRoleSet:
        role_set, game = await self._set_and_game(role_set_id)
        if game.server_id is None:
            raise ForbiddenException("Unable to edit a global game role set")
        if game.server_id != server_id:
            raise NotFoundException("Role set not found for server")
        return role_set

    async def _require_global_set(self, role_set_id: UUID) -> GameRoleSet:
        role_set, game = await self._set_and_game(role_set_id)
        if game.server_id is not None:
            raise ForbiddenException("Role set does not belong to a global game")
        return role_set

    async def _require_local_role(self, server_id: UUID, role_id: UUID) -> GameRole:
        role = await self.role_repo.get(role_id)
        if role is None:
            raise NotFoundException("Role not found")
        await self._require_local_set(server_id, role.role_set_id)
        return role

    async def _require_global_role(self, role_id: UUID) -> GameRole:
        role = await self.role_repo.get(role_id)
        if role is None:
            raise NotFoundException("Role not found")
        await self._require_global_set(role.role_set_id)
        return role

    async def update_role_set(
            self, server_id: UUID, role_set_id: UUID, name: str | None = None, permission_mask: int = 0
    ) -> GameRoleSetDetail:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_set_field = await self._require_local_set(server_id, role_set_id)
        if name is not None and name != role_set_field.name:
            await self.role_set_repo.update(GameRoleSetUpdate(id=role_set_id, name=name))
        role_set_detail = await self.role_set_repo.get_detail(role_set_id)
        if role_set_detail is None:
            raise InternalLogicException("Role set not found")
        return role_set_detail

    async def update_global_role_set(self, role_set_id: UUID, name: str | None = None) -> GameRoleSetDetail:
        role_set_field = await self._require_global_set(role_set_id)
        if name is not None and name != role_set_field.name:
            await self.role_set_repo.update(GameRoleSetUpdate(id=role_set_id, name=name))
        role_set_detail = await self.role_set_repo.get_detail(role_set_id)
        if role_set_detail is None:
            raise InternalLogicException("Role set not found")
        return role_set_detail

    async def _create_role(
            self,
            role_set_id: UUID,
            name: str,
            min_in_team: int,
            max_in_team: int,
            icon_id: UUID | None,
            hidden: bool,
    ) -> GameRole:
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

    async def create_role(
            self,
            server_id: UUID,
            role_set_id: UUID,
            name: str,
            min_in_team: int,
            max_in_team: int,
            icon_id: UUID | None = None,
            hidden: bool = False,
            permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        await self._require_local_set(server_id, role_set_id)
        return await self._create_role(role_set_id, name, min_in_team, max_in_team, icon_id, hidden)

    async def create_global_role(
            self,
            role_set_id: UUID,
            name: str,
            min_in_team: int,
            max_in_team: int,
            icon_id: UUID | None = None,
            hidden: bool = False,
    ) -> GameRole:
        await self._require_global_set(role_set_id)
        return await self._create_role(role_set_id, name, min_in_team, max_in_team, icon_id, hidden)

    async def _apply_role_update(
            self,
            role: GameRole,
            name: str | None = None,
            min_in_team: int | None = None,
            max_in_team: int | None = None,
            icon_id: UUID | None = None,
            hidden: bool | None = None,
    ) -> GameRole:
        update_data: dict = {}
        if name is not None and name != role.name:
            update_data["name"] = name
        if hidden is not None and hidden != role.hidden:
            update_data["hidden"] = hidden
        if min_in_team is not None:
            update_data["min_in_team"] = min_in_team
        if max_in_team is not None:
            update_data["max_in_team"] = max_in_team
        if icon_id is not None:
            update_data["icon_id"] = icon_id

        if update_data:
            role = await self.role_repo.update(GameRoleUpdate(id=role.id, **update_data))
        return role

    async def update_role(
            self,
            server_id: UUID,
            role_id: UUID,
            name: str | None = None,
            min_in_team: int | None = None,
            max_in_team: int | None = None,
            icon_id: UUID | None = None,
            hidden: bool | None = None,
            permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_field = await self._require_local_role(server_id, role_id)
        return await self._apply_role_update(role_field, name, min_in_team, max_in_team, icon_id, hidden)

    async def update_global_role(
            self,
            role_id: UUID,
            name: str | None = None,
            min_in_team: int | None = None,
            max_in_team: int | None = None,
            icon_id: UUID | None = None,
            hidden: bool | None = None,
    ) -> GameRole:
        role_field = await self._require_global_role(role_id)
        return await self._apply_role_update(role_field, name, min_in_team, max_in_team, icon_id, hidden)

    async def delete_role(self, server_id: UUID, role_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to delete role")
        await self._require_local_role(server_id, role_id)
        deleted = await self.role_repo.delete(role_id)
        if not deleted:
            raise NotFoundException("Role not found")

    async def delete_global_role(self, role_id: UUID) -> None:
        await self._require_global_role(role_id)
        deleted = await self.role_repo.delete(role_id)
        if not deleted:
            raise NotFoundException("Role not found")

    async def delete_role_icon(self, server_id: UUID, role_id: UUID, permission_mask: int = 0) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_field = await self._require_local_role(server_id, role_id)
        return await self.role_repo.update(GameRoleUpdate(id=role_field.id, icon_id=None))

    async def delete_global_role_icon(self, role_id: UUID) -> GameRole:
        role_field = await self._require_global_role(role_id)
        return await self.role_repo.update(GameRoleUpdate(id=role_field.id, icon_id=None))
