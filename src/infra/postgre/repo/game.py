from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Game, ServerGame


class GameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, game_id: UUID) -> Game | None:
        stmt = select(Game).where(Game.id == game_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> Game | None:
        stmt = select(Game).where(Game.name == name).limit(1)
        return await self.session.scalar(stmt)

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

    async def add_to_server(self, game_id: UUID, server_id: UUID) -> None:
        stmt = select(ServerGame).where(
            ServerGame.game_id == game_id,
            ServerGame.server_id == server_id
        ).limit(1)
        existing = await self.session.scalar(stmt)
        if existing:
            return
        link = ServerGame(game_id=game_id, server_id=server_id)
        self.session.add(link)
        await self.session.flush()

    async def remove_from_server(self, game_id: UUID, server_id: UUID) -> bool:
        stmt = delete(ServerGame).where(
            ServerGame.game_id == game_id,
            ServerGame.server_id == server_id
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return bool(result.rowcount)    # type: ignore

    async def bulk_add_to_server(self, server_id: UUID, game_ids: list[UUID]) -> None:
        for gid in game_ids:
            await self.add_to_server(gid, server_id)
