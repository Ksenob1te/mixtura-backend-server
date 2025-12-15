# Deprecated: replaced by restriction_code.py and member_restriction.py

from uuid import UUID
from datetime import datetime
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Restriction


class RestrictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, code_id: UUID) -> Restriction | None:
        stmt = select(Restriction).where(Restriction.id == code_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_code(self, code: str) -> Restriction | None:
        stmt = select(Restriction).where(Restriction.code == code).limit(1)
        return await self.session.scalar(stmt)

    async def list_all(self) -> Sequence[Restriction]:
        stmt = select(Restriction)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, code: str) -> Restriction | None:
        # TODO: handle integrity errors
        rc = Restriction(code=code)
        self.session.add(rc)
        await self.session.flush()
        return await self.get_by_id(rc.id)

    async def delete(self, code_id: UUID) -> bool:
        stmt = delete(Restriction).where(Restriction.id == code_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def get_by_code_bulk(self, codes: Sequence[str]) -> Sequence[Restriction]:
        stmt = select(Restriction).where(Restriction.code.in_(codes))
        res = await self.session.scalars(stmt)
        return res.all()

