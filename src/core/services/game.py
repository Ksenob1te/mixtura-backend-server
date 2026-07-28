from uuid import UUID

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.game import GameRepositoryProtocol
from src.core.interfaces.repo.game_role import GameRoleRepositoryProtocol
from src.core.interfaces.repo.game_role_set import GameRoleSetRepositoryProtocol
from src.core.interfaces.repo.rating import RatingRepositoryProtocol
from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.game import Game, GameCreate, GameDetail, GameUpdate
from src.core.models.game_role import GameRoleCreate
from src.core.models.game_role_set import GameRoleSet, GameRoleSetCreate
from src.core.models.rating_set import RatingSet, RatingSetCreate
from src.infra.postgre.static import PERMISSION


class GameService:
    def __init__(
        self,
        game_repo: GameRepositoryProtocol,
        server_repo: ServerRepositoryProtocol,
        game_role_set_repo: GameRoleSetRepositoryProtocol,
        rating_set_repo: RatingSetRepositoryProtocol,
        game_role_repo: GameRoleRepositoryProtocol,
        rating_repo: RatingRepositoryProtocol,
    ) -> None:
        self.game_repo = game_repo
        self.server_repo = server_repo
        self.game_role_set_repo = game_role_set_repo
        self.rating_set_repo = rating_set_repo
        self.game_role_repo = game_role_repo
        self.rating_repo = rating_repo

    async def _create_game_shell(
        self,
        name: str,
        min_rating: int,
        max_rating: int,
        icon_id: UUID | None,
        banner_id: UUID | None,
        server_id: UUID | None,
    ) -> tuple[Game, GameRoleSet, RatingSet]:
        if min_rating > max_rating:
            raise BadRequestException("Rating bounds are invalid")

        try:
            game = await self.game_repo.create(
                GameCreate(name=name, server_id=server_id, icon_id=icon_id, banner_id=banner_id)
            )
        except IntegrityUniqueException:
            raise BadRequestException("Game name is already taken")
        except IntegrityForeignException:
            raise NotFoundException("Server not found")
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)

        role_set = await self.game_role_set_repo.create(GameRoleSetCreate(name=name, game_id=game.id))
        rating_set = await self.rating_set_repo.create(
            RatingSetCreate(name=name, min_rating=min_rating, max_rating=max_rating, game_id=game.id)
        )
        return game, role_set, rating_set

    async def _build_game(
        self,
        name: str,
        min_rating: int,
        max_rating: int,
        icon_id: UUID | None,
        banner_id: UUID | None,
        server_id: UUID | None,
    ) -> GameDetail:
        game, role_set, _rating_set = await self._create_game_shell(
            name, min_rating, max_rating, icon_id, banner_id, server_id
        )
        await self.game_role_repo.create(
            GameRoleCreate(name="Leader", role_set_id=role_set.id, min_in_team=1, max_in_team=1, hidden=False)
        )
        detail = await self.game_repo.get_detail(game.id)
        if detail is None:
            raise InternalLogicException("Failed to create game")
        return detail

    async def _require_global(self, game_id: UUID) -> Game:
        game = await self.game_repo.get(game_id)
        if not game:
            raise NotFoundException("Game not found")
        if game.server_id is not None:
            raise ForbiddenException("Game is not a global game")
        return game

    async def _require_local(self, server_id: UUID, game_id: UUID) -> Game:
        game = await self.game_repo.get(game_id)
        if not game:
            raise NotFoundException("Game not found")
        if game.server_id is None:
            raise ForbiddenException("Unable to edit a global game")
        if game.server_id != server_id:
            raise NotFoundException("Game not found on server")
        return game

    async def _assert_selectable(self, server_id: UUID, game_ids: list[UUID]) -> None:
        for game_id in game_ids:
            game = await self.game_repo.get(game_id)
            if not game:
                raise NotFoundException("Game not found")
            if game.server_id is not None and game.server_id != server_id:
                raise NotFoundException("Game not found")

    async def list_global_games(self) -> list[GameDetail]:
        return list(await self.game_repo.list_global())

    async def create_global_game(
        self,
        name: str,
        min_rating: int,
        max_rating: int,
        icon_id: UUID | None = None,
        banner_id: UUID | None = None,
    ) -> GameDetail:
        return await self._build_game(name, min_rating, max_rating, icon_id, banner_id, server_id=None)

    async def update_global_game(
        self,
        game_id: UUID,
        name: str | None = None,
        icon_id: UUID | None = None,
        banner_id: UUID | None = None,
    ) -> GameDetail:
        game = await self._require_global(game_id)

        update_data: dict = {}
        if name is not None and name != game.name:
            update_data["name"] = name
        if icon_id is not None and icon_id != game.icon_id:
            update_data["icon_id"] = icon_id
        if banner_id is not None and banner_id != game.banner_id:
            update_data["banner_id"] = banner_id

        if update_data:
            try:
                await self.game_repo.update(GameUpdate(id=game_id, **update_data))
            except IntegrityUniqueException:
                raise BadRequestException("Game name is already taken")

        detail = await self.game_repo.get_detail(game_id)
        if detail is None:
            raise InternalLogicException("Game not found")
        return detail

    async def delete_global_game(self, game_id: UUID) -> None:
        await self._require_global(game_id)
        ok = await self.game_repo.delete(game_id)
        if not ok:
            raise InternalLogicException("Failed to delete game")

    async def list_server_games(self, server_id: UUID) -> list[GameDetail]:
        if not await self.server_repo.get(server_id):
            raise NotFoundException("Server not found")
        return list(await self.game_repo.list_for_server(server_id))

    async def list_owned_games(self, server_id: UUID) -> list[GameDetail]:
        if not await self.server_repo.get(server_id):
            raise NotFoundException("Server not found")
        return list(await self.game_repo.list_owned_by_server(server_id))

    async def create_local_game(
        self,
        server_id: UUID,
        name: str,
        min_rating: int,
        max_rating: int,
        icon_id: UUID | None = None,
        banner_id: UUID | None = None,
        permission_mask: int = 0,
    ) -> GameDetail:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        if not await self.server_repo.get(server_id):
            raise NotFoundException("Server not found")

        detail = await self._build_game(name, min_rating, max_rating, icon_id, banner_id, server_id=server_id)
        await self.game_repo.add_to_server(detail.id, server_id)
        return detail

    async def copy_global_game(
        self,
        server_id: UUID,
        game_id: UUID,
        permission_mask: int = 0,
    ) -> GameDetail:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        if not await self.server_repo.get(server_id):
            raise NotFoundException("Server not found")

        source = await self.game_repo.get_detail(game_id)
        if source is None:
            raise NotFoundException("Game not found")
        if source.server_id is not None:
            raise ForbiddenException("Game is not a global game")

        new_game, new_role_set, new_rating_set = await self._create_game_shell(
            source.name,
            source.rating_set.min_rating,
            source.rating_set.max_rating,
            source.icon_id,
            source.banner_id,
            server_id=server_id,
        )
        for role in source.role_set.game_roles:
            await self.game_role_repo.copy_role(role, new_role_set.id)
        for rating in source.rating_set.ratings:
            await self.rating_repo.copy_rating(rating, new_rating_set.id)

        await self.game_repo.add_to_server(new_game.id, server_id)

        detail = await self.game_repo.get_detail(new_game.id)
        if detail is None:
            raise InternalLogicException("Failed to copy game")
        return detail

    async def update_local_game(
        self,
        server_id: UUID,
        game_id: UUID,
        name: str | None = None,
        icon_id: UUID | None = None,
        banner_id: UUID | None = None,
        permission_mask: int = 0,
    ) -> GameDetail:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        game = await self._require_local(server_id, game_id)

        update_data: dict = {}
        if name is not None and name != game.name:
            update_data["name"] = name
        if icon_id is not None and icon_id != game.icon_id:
            update_data["icon_id"] = icon_id
        if banner_id is not None and banner_id != game.banner_id:
            update_data["banner_id"] = banner_id

        if update_data:
            try:
                await self.game_repo.update(GameUpdate(id=game_id, **update_data))
            except IntegrityUniqueException:
                raise BadRequestException("Game name is already taken")

        detail = await self.game_repo.get_detail(game_id)
        if detail is None:
            raise InternalLogicException("Game not found")
        return detail

    async def delete_local_game(
        self,
        server_id: UUID,
        game_id: UUID,
        permission_mask: int = 0,
    ) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        await self._require_local(server_id, game_id)
        ok = await self.game_repo.delete(game_id)
        if not ok:
            raise InternalLogicException("Failed to delete game")

    async def add_games_to_server(
        self,
        server_id: UUID,
        game_ids: list[UUID],
        permission_mask: int = 0,
    ) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        if not game_ids:
            return
        await self._assert_selectable(server_id, game_ids)
        try:
            await self.game_repo.bulk_add_to_server(server_id, game_ids)
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUniqueException, IntegrityUnknownException) as exc:
            raise InternalLogicException(exc.message)

    async def remove_game_from_server(
        self,
        server_id: UUID,
        game_id: UUID,
        permission_mask: int = 0,
    ) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to manage server games")

        removed = await self.game_repo.remove_from_server(game_id, server_id)
        if not removed:
            raise NotFoundException("Game not found on server")

    async def set_server_games(
            self,
            server_id: UUID,
            game_ids: list[UUID],
            permission_mask: int = 0,
    ) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        await self._assert_selectable(server_id, game_ids)
        await self.game_repo.set_server_games(server_id, game_ids)
