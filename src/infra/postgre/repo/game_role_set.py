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

    async def get_global(self) -> Sequence[GameRoleSet]:
        stmt = select(GameRoleSet).where(GameRoleSet.is_global.is_(True))
        res = await self.session.scalars(stmt)
        return res.all()

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

    async def copy_global(self, global_set_id: UUID) -> GameRoleSet | None:
        # TODO: add tests for this method
        global_set = await self.get_by_id(global_set_id)
        if not global_set or not global_set.is_global:
            return None
        new_set = GameRoleSet(name=global_set.name, is_global=False)
        self.session.add(new_set)
        await self.session.flush()
        return await self.get_by_id(new_set.id)
