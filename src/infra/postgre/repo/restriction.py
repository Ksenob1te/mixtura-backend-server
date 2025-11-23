from uuid import UUID
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Restriction


class RestrictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, restriction_id: UUID) -> Restriction | None:
        stmt = select(Restriction).where(Restriction.id == restriction_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_member(self, member_id: UUID) -> Sequence[Restriction]:
        stmt = select(Restriction).where(Restriction.member_id == member_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_active_for_member(self, member_id: UUID, now: datetime | None = None) -> Sequence[Restriction]:
        if now is None:
            now = datetime.now(timezone.utc)
        stmt = select(Restriction).where(
            Restriction.member_id == member_id,
            Restriction.expiration_date > now
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, member_id: UUID, reason: str, expiration_date: datetime,
                     type_code: str) -> Restriction | None:
        r = Restriction(member_id=member_id, reason=reason, expiration_date=expiration_date, type_code=type_code)
        self.session.add(r)
        await self.session.flush()
        return await self.get_by_id(r.id)

    async def set_reason(self, restriction: Restriction, reason: str) -> Restriction:
        restriction.reason = reason
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def set_expiration(self, restriction: Restriction, expiration_date: datetime) -> Restriction:
        restriction.expiration_date = expiration_date
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def set_type_code(self, restriction: Restriction, type_code: str) -> Restriction:
        restriction.type_code = type_code
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def delete(self, restriction_id: UUID) -> bool:
        stmt = delete(Restriction).where(Restriction.id == restriction_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
