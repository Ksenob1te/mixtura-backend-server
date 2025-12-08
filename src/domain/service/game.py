from uuid import UUID

from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.infra.postgre.models import Game
from src.infra.postgre.repo import GameRepository, ServerRepository
from src.infra.postgre.static import PERMISSION

from sqlalchemy.exc import IntegrityError


class GameService:
    def __init__(
        self,
        game_repo: GameRepository,
        server_repo: ServerRepository,
    ) -> None:
        self.game_repo = game_repo
        self.server_repo = server_repo

    async def list_server_games(self, server_id: UUID) -> list[Game]:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server.games     # type: ignore

    async def add_games_to_server(
        self,
        server_id: UUID,
        game_ids: list[UUID],
        permission_mask: int = 0,
    ) -> None:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to edit server games")
        if not game_ids:
            return
        try:
            await self.game_repo.bulk_add_to_server(server_id, game_ids)
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some games do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise NotFoundException("Some games are not found")
            raise InternalLogicException("Failed to add games to server")

    async def remove_game_from_server(
        self,
        server_id: UUID,
        game_id: UUID,
        permission_mask: int = 0,
    ) -> None:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")

        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_GAME):
            raise ForbiddenException("Unable to manage server games")

        removed = await self.game_repo.remove_from_server(game_id, server_id)
        if not removed:
            raise NotFoundException("Game not found on server")
