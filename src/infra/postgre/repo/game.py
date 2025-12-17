from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Game, ServerGame
from sqlalchemy.dialects.postgresql import insert

from ..exceptions import IntegrityUniqueException, IntegrityUnknownException, IntegrityForeignException


class GameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, game_id: UUID) -> Game | None:
        stmt = select(Game).where(Game.id == game_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> Game | None:
        stmt = select(Game).where(Game.name == name).limit(1)
        return await self.session.scalar(stmt)

    async def get_all(self) -> Sequence[Game]:
        stmt = select(Game)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, name: str, icon_id: UUID, banner_id: UUID) -> Game:
        game = Game(name=name, icon_id=icon_id, banner_id=banner_id)
        try:
            self.session.add(game)
            await self.session.flush()
            game_field = await self.get_by_id(game.id)
            if game_field is None:
                raise IntegrityUnknownException("Failed to create game")
            return game_field
        except IntegrityError as exc:
            # SQLSTATE_UNIQUE_VIOLATION - game with this name already exists
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23505":
                raise IntegrityUniqueException("Game with this name already exists")
            raise IntegrityUnknownException("Failed to create game")

    async def set_name(self, game: Game, name: str) -> Game:
        game.name = name
        await self.session.flush()
        return game

    async def set_icon(self, game: Game, icon_id: UUID) -> Game:
        game.icon_id = icon_id
        await self.session.flush()
        return game

    async def set_banner(self, game: Game, banner_id: UUID) -> Game:
        game.banner_id = banner_id
        await self.session.flush()
        return game

    async def delete(self, game_id: UUID) -> bool:
        stmt = delete(Game).where(Game.id == game_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)    # type: ignore

    async def add_to_server(self, game_id: UUID, server_id: UUID) -> ServerGame:
        try:
            stmt = (
                insert(ServerGame)
                .values(game_id=game_id, server_id=server_id)
                .on_conflict_do_nothing(
                    index_elements=[ServerGame.game_id, ServerGame.server_id]
                )
                .returning(ServerGame)
            )

            result = await self.session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is not None:
                return row

            stmt = select(ServerGame).where(
                ServerGame.game_id == game_id,
                ServerGame.server_id == server_id
            ).limit(1)
            existing = await self.session.scalar(stmt)
            if existing is not None:
                return existing

        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            if sql_state == "23503":
                raise IntegrityForeignException("Game or server fields are not found")
        raise IntegrityUnknownException("Failed to add game to server")

    async def remove_from_server(self, game_id: UUID, server_id: UUID) -> bool:
        stmt = delete(ServerGame).where(
            ServerGame.game_id == game_id,
            ServerGame.server_id == server_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)    # type: ignore

    async def bulk_add_to_server(self, server_id: UUID, game_ids: list[UUID]) -> list[ServerGame]:
        stmt = (
            insert(ServerGame)
            .values(
                [
                    {
                        "server_id": server_id,
                        "game_id": gid,
                    }
                    for gid in game_ids
                ]
            )
            .on_conflict_do_nothing(
                index_elements=[
                    ServerGame.server_id,
                    ServerGame.game_id,
                ]
            )
            .returning(ServerGame)
        )

        try:
            result = await self.session.execute(stmt)
            await self.session.flush()
            return list(result.scalars().all())
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Some games are not found")
            raise IntegrityUnknownException("Failed to add games to server")
