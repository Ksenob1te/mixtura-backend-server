from uuid import UUID
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import MemberRestriction

from ..exceptions import IntegrityUnknownException, IntegrityForeignException


class MemberRestrictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, restriction_id: UUID) -> MemberRestriction | None:
        stmt = select(MemberRestriction).where(MemberRestriction.id == restriction_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_member(self, member_id: UUID) -> Sequence[MemberRestriction]:
        stmt = select(MemberRestriction).where(MemberRestriction.member_id == member_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_active_for_member(self, member_id: UUID, now: datetime | None = None) -> Sequence[MemberRestriction]:
        if now is None:
            now = datetime.now(timezone.utc)
        stmt = select(MemberRestriction).where(
            MemberRestriction.member_id == member_id,
            MemberRestriction.expiration_date > now
        )
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, member_id: UUID, restriction_id: UUID, reason: str,
                     expiration_date: datetime, creator_id: UUID) -> MemberRestriction:
        r = MemberRestriction(
            member_id=member_id,
            restriction_id=restriction_id,
            reason=reason,
            expiration_date=expiration_date,
            creator_id=creator_id,
        )
        try:
            self.session.add(r)
            await self.session.flush()
            member_restriction_field = await self.get_by_id(r.id)
            if member_restriction_field is None:
                raise IntegrityUnknownException("Failed to create member restriction")
            return member_restriction_field
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Member, restriction code or creator fields are not found")
            raise IntegrityUnknownException("Failed to create member restriction")

    async def set_reason(self, restriction: MemberRestriction, reason: str) -> MemberRestriction:
        restriction.reason = reason
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def set_expiration(self, restriction: MemberRestriction, expiration_date: datetime) -> MemberRestriction:
        restriction.expiration_date = expiration_date
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def set_code(self, restriction: MemberRestriction, restriction_code_id: UUID) -> MemberRestriction:
        restriction.restriction_id = restriction_code_id
        self.session.add(restriction)
        await self.session.flush()
        return restriction

    async def delete(self, restriction_id: UUID) -> bool:
        stmt = delete(MemberRestriction).where(MemberRestriction.id == restriction_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
