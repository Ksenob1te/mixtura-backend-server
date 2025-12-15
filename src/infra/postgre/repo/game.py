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

    async def create(self, name: str, icon_url: str, banner_url: str) -> Game | None:
        game = Game(name=name, icon_url=icon_url, banner_url=banner_url)
        self.session.add(game)
        await self.session.flush()
        return await self.get_by_id(game.id)

    async def set_name(self, game: Game, name: str) -> Game:
        game.name = name
        self.session.add(game)
        await self.session.flush()
        return game

    async def set_icon(self, game: Game, icon_url: str) -> Game:
        game.icon_url = icon_url
        self.session.add(game)
        await self.session.flush()
        return game

    async def set_banner(self, game: Game, banner_url: str) -> Game:
        game.banner_url = banner_url
        self.session.add(game)
        await self.session.flush()
        return game

    async def delete(self, game_id: UUID) -> bool:
        stmt = delete(Game).where(Game.id == game_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)    # type: ignore

    async def add_to_server(self, game_id: UUID, server_id: UUID) -> ServerGame:
        stmt = select(ServerGame).where(
            ServerGame.game_id == game_id,
            ServerGame.server_id == server_id
        ).limit(1)
        existing = await self.session.scalar(stmt)
        if existing:
            return existing
        link = ServerGame(game_id=game_id, server_id=server_id)
        self.session.add(link)
        await self.session.flush()
        return link

    async def remove_from_server(self, game_id: UUID, server_id: UUID) -> bool:
        stmt = delete(ServerGame).where(
            ServerGame.game_id == game_id,
            ServerGame.server_id == server_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)    # type: ignore

    async def bulk_add_to_server(self, server_id: UUID, game_ids: list[UUID]) -> Sequence[ServerGame]:
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
            return result.scalars().all()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Some games are not found")
            raise IntegrityUnknownException("Failed to add games to server")


