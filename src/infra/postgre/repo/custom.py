from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Custom


class CustomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, custom_id: UUID) -> Custom | None:
        stmt = select(Custom).where(Custom.id == custom_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_member(self, member_id: UUID) -> Sequence[Custom]:
        stmt = select(Custom).where(Custom.member_id == member_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, member_id: UUID, creator_id: UUID | None = None) -> Custom | None:
        custom = Custom(member_id=member_id, creator_id=creator_id)
        self.session.add(custom)
        await self.session.flush()
        return await self.get_by_id(custom.id)

    async def set_creator(self, custom: Custom, creator_id: UUID) -> Custom:
        if custom.creator_id == creator_id:
            return custom
        custom.creator_id = creator_id
        self.session.add(custom)
        await self.session.flush()
        return custom

    async def delete(self, custom_id: UUID) -> bool:
        stmt = delete(Custom).where(Custom.id == custom_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
