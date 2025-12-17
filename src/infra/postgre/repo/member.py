from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..models import Member

from ..exceptions import IntegrityUniqueException, IntegrityUnknownException, IntegrityForeignException


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

    async def create(self, server_id: UUID, user_id: UUID | None, name: str,
                     server_role_id: UUID | None = None) -> Member:
        member_field = Member(server_id=server_id, user_id=user_id, name=name, server_role_id=server_role_id)
        try:
            self.session.add(member_field)
            await self.session.flush()
            member_field = await self.get_by_id(member_field.id)
            if member_field is None:
                raise IntegrityUnknownException("Failed to create member")
            return member_field
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException("Server, user or server role fields are not found") from exc
            # SQLSTATE_UNIQUE_VIOLATION - user is already a member of this server
            if sql_state == "23505":
                raise IntegrityUniqueException("User is already a member of this server") from exc
            raise IntegrityUnknownException("Failed to create member") from exc

    async def set_role(self, member: Member, server_role_id: UUID | None) -> Member:
        if member.server_role_id == server_role_id:
            return member
        member.server_role_id = server_role_id
        self.session.add(member)
        await self.session.flush()
        return member

    async def set_name(self, member: Member, name: str) -> Member:
        if member.name == name:
            return member
        member.name = name
        self.session.add(member)
        await self.session.flush()
        return member

    async def set_user_if_none(self, member: Member, user_id: UUID) -> bool:
        if member.user_id is not None:
            return False

        conflict_exists = select(Member.id).where(
            Member.server_id == member.server_id,
            Member.user_id == user_id
        ).exists()

        stmt = (
            update(Member)
            .where(Member.id == member.id)
            .where(Member.user_id.is_(None))
            .where(~conflict_exists)
            .values(user_id=user_id)
            .returning(Member.id)
        )
        res = await self.session.execute(stmt)
        success = res.scalar_one_or_none() is not None
        if success:
            member.user_id = user_id
            await self.session.flush()
            return True
        return False

    async def remove_user(self, member: Member) -> Member:
        if member.user_id is None:
            return member
        member.user_id = None
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
