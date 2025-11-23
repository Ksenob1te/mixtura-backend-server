from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Member


class MemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, member_id: UUID) -> Member | None:
        stmt = select(Member).where(Member.id == member_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_user_in_server(self, server_id: UUID, user_id: UUID) -> Member | None:
        stmt = select(Member).where(Member.server_id == server_id, Member.user_id == user_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_server(self, server_id: UUID) -> Sequence[Member]:
        stmt = select(Member).where(Member.server_id == server_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def list_active_for_server(self, server_id: UUID) -> Sequence[Member]:
        stmt = select(Member).where(Member.server_id == server_id, Member.active.is_(True))
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, server_id: UUID, user_id: UUID | None, server_role_id: UUID | None = None) -> Member | None:
        m = Member(server_id=server_id, user_id=user_id, server_role_id=server_role_id)
        self.session.add(m)
        await self.session.flush()
        return await self.get_by_id(m.id)

    async def set_role(self, member: Member, server_role_id: UUID | None) -> Member:
        if member.server_role_id == server_role_id:
            return member
        member.server_role_id = server_role_id
        self.session.add(member)
        await self.session.flush()
        return member

    async def deactivate(self, member: Member) -> Member:
        if not member.active:
            return member
        member.active = False
        self.session.add(member)
        await self.session.flush()
        return member

    async def activate(self, member: Member) -> Member:
        if member.active:
            return member
        member.active = True
        self.session.add(member)
        await self.session.flush()
        return member

    async def delete(self, member_id: UUID) -> bool:
        stmt = delete(Member).where(Member.id == member_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
