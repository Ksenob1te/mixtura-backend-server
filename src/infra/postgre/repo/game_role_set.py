from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import GameRoleSet


class GameRoleSetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_set_id: UUID) -> GameRoleSet | None:
        stmt = select(GameRoleSet).where(GameRoleSet.id == role_set_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> GameRoleSet | None:
        stmt = select(GameRoleSet).where(GameRoleSet.name == name).limit(1)
        return await self.session.scalar(stmt)

    async def create(self, name: str, is_global: bool = False) -> GameRoleSet | None:
        rs = GameRoleSet(name=name, is_global=is_global)
        self.session.add(rs)
        await self.session.flush()
        return await self.get_by_id(rs.id)

    async def set_name(self, role_set: GameRoleSet, name: str) -> GameRoleSet:
        role_set.name = name
        self.session.add(role_set)
        await self.session.flush()
        return role_set

    async def set_global(self, role_set: GameRoleSet, is_global: bool) -> GameRoleSet:
        role_set.is_global = is_global
        self.session.add(role_set)
        await self.session.flush()
        return role_set

    async def delete(self, role_set_id: UUID) -> bool:
        stmt = delete(GameRoleSet).where(GameRoleSet.id == role_set_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
