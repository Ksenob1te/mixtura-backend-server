from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import IntegrityForeignException, IntegrityUnknownException
from src.core.interfaces.repo.game import GameRepositoryProtocol
from src.core.models.game import Game as GameDTO
from src.core.models.game import GameCreate, GameDetail, GameUpdate
from src.core.models.server_game import ServerGame as ServerGameDTO

from ..models import Game as GameModel
from ..models import ServerGame as ServerGameModel
from .base import BaseRepository


class GameRepository(
    BaseRepository[GameModel, GameCreate, GameDTO, GameUpdate],
    GameRepositoryProtocol,
):
    model = GameModel
    dto_model = GameDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    @staticmethod
    def _to_detail_dto(obj: GameModel) -> GameDetail:
        return GameDetail.model_validate(obj, from_attributes=True)

    async def get_detail(self, game_id: UUID) -> GameDetail | None:
        obj = await self._get_model(game_id)
        return self._to_detail_dto(obj) if obj else None

    async def get_by_name(self, name: str, server_id: UUID | None = None) -> GameDTO | None:
        stmt = select(GameModel).where(GameModel.name == name)
        stmt = stmt.where(GameModel.server_id.is_(None)) if server_id is None else stmt.where(
            GameModel.server_id == server_id
        )
        result = await self._session.scalar(stmt.limit(1))
        return self._to_dto(result) if result else None

    async def list_global(self) -> Sequence[GameDetail]:
        stmt = select(GameModel).where(GameModel.server_id.is_(None))
        res = await self._session.scalars(stmt)
        return [self._to_detail_dto(item) for item in res.all()]

    async def list_owned_by_server(self, server_id: UUID) -> Sequence[GameDetail]:
        stmt = select(GameModel).where(GameModel.server_id == server_id)
        res = await self._session.scalars(stmt)
        return [self._to_detail_dto(item) for item in res.all()]

    async def list_for_server(self, server_id: UUID) -> Sequence[GameDetail]:
        stmt = select(GameModel).join(
            ServerGameModel, GameModel.id == ServerGameModel.game_id
        ).where(ServerGameModel.server_id == server_id)
        res = await self._session.scalars(stmt)
        return [self._to_detail_dto(item) for item in res.all()]

    async def is_enabled_on_server(self, server_id: UUID, game_id: UUID) -> bool:
        stmt = select(func.count()).select_from(ServerGameModel).where(
            ServerGameModel.server_id == server_id, ServerGameModel.game_id == game_id
        )
        count = await self._session.scalar(stmt)
        return (count or 0) > 0

    @staticmethod
    def _to_server_game_dto(obj: ServerGameModel) -> ServerGameDTO:
        return ServerGameDTO.model_validate(obj, from_attributes=True)

    async def add_to_server(self, game_id: UUID, server_id: UUID) -> ServerGameDTO:
        try:
            stmt = (
                insert(ServerGameModel)
                .values(game_id=game_id, server_id=server_id)
                .on_conflict_do_nothing(
                    index_elements=[ServerGameModel.game_id, ServerGameModel.server_id]
                )
                .returning(ServerGameModel)
            )

            result = await self._session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is not None:
                return self._to_server_game_dto(row)

            stmt = select(ServerGameModel).where(
                ServerGameModel.game_id == game_id,
                ServerGameModel.server_id == server_id
            ).limit(1)
            existing = await self._session.scalar(stmt)
            if existing is not None:
                return self._to_server_game_dto(existing)

        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Game or server fields are not found")
        raise IntegrityUnknownException("Failed to add game to server")

    async def remove_from_server(self, game_id: UUID, server_id: UUID) -> bool:
        stmt = delete(ServerGameModel).where(
            ServerGameModel.game_id == game_id,
            ServerGameModel.server_id == server_id
        )
        return bool(await self._execute_dml(stmt))

    async def bulk_add_to_server(self, server_id: UUID, game_ids: list[UUID]) -> list[ServerGameDTO]:
        stmt = (
            insert(ServerGameModel)
            .values(
                [{"server_id": server_id, "game_id": gid} for gid in game_ids]
            )
            .on_conflict_do_nothing(
                index_elements=[
                    ServerGameModel.game_id,
                    ServerGameModel.server_id,
                ]
            )
            .returning(ServerGameModel)
        )

        try:
            result = await self._session.execute(stmt)
            await self._flush()
            rows = result.scalars().all()
            if rows:
                return [self._to_server_game_dto(row) for row in rows]
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Game or server fields are not found")
            raise IntegrityUnknownException("Failed to add games to server")

        stmt = select(ServerGameModel).where(
            ServerGameModel.server_id == server_id,
            ServerGameModel.game_id.in_(game_ids),
        )
        res = await self._session.scalars(stmt)
        return [self._to_server_game_dto(item) for item in res.all()]

    async def bulk_remove_from_server(self, server_id: UUID, game_ids: list[UUID]) -> int:
        stmt = delete(ServerGameModel).where(
            ServerGameModel.server_id == server_id,
            ServerGameModel.game_id.in_(game_ids)
        )
        return await self._execute_dml(stmt)

    async def set_server_games(self, server_id: UUID, game_ids: list[UUID]) -> None:
        stmt = select(ServerGameModel).where(ServerGameModel.server_id == server_id)
        res = await self._session.scalars(stmt)
        existing_links = res.all()

        existing_ids = {link.game_id for link in existing_links}
        target_ids = set(game_ids)

        to_add_ids = target_ids - existing_ids
        to_remove_ids = existing_ids - target_ids

        if to_add_ids:
            await self.bulk_add_to_server(server_id, list(to_add_ids))
        if to_remove_ids:
            await self.bulk_remove_from_server(server_id, list(to_remove_ids))
