from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.game import GameRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.game import Game
from src.infra.postgre.static import PERMISSION


class GameService:
    def __init__(
        self,
        game_repo: GameRepositoryProtocol,
        server_repo: ServerRepositoryProtocol,
    ) -> None:
        self.game_repo = game_repo
        self.server_repo = server_repo

    async def list_server_games(self, server_id: UUID) -> list[Game]:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        games = await self.game_repo.list_for_server(server_id)
        return list(games)

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
        await self.game_repo.set_server_games(server_id, game_ids)
