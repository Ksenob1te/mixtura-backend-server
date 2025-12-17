from uuid import UUID
import secrets
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Invite

from ..exceptions import (IntegrityUniqueException, IntegrityUnknownException, IntegrityForeignException,
                          InviteUniqueException)


class InviteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, invite_id: UUID) -> Invite | None:
        stmt = select(Invite).where(Invite.id == invite_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_key(self, key: str) -> Invite | None:
        stmt = select(Invite).where(Invite.key == key).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_server(self, server_id: UUID) -> Sequence[Invite]:
        stmt = select(Invite).where(Invite.server_id == server_id)
        res = await self.session.scalars(stmt)
        return res.all()

    @staticmethod
    async def _generate_key(length: int = 12) -> str:
        raw = secrets.token_urlsafe(length)
        return raw.replace('-', '').replace('_', '')[:length]

    async def create(self, server_id: UUID, use_limit: int, inviter_id: UUID | None = None,
                     key: str | None = None) -> Invite:
        values: dict[str, str | int | UUID | None] = {
            "server_id": server_id,
            "inviter_id": inviter_id,
            "use_limit": use_limit,
        }

        if key is not None:
            values["key"] = key
            stmt = (
                insert(Invite)
                .values(**values)
                .returning(Invite)
            )
            try:
                result = await self.session.execute(stmt)
                return result.scalar_one()
            except IntegrityError as exc:
                # SQLSTATE_UNIQUE_VIOLATION - key is not unique
                sql_state = getattr(exc.orig, "sqlstate", None)
                if sql_state == "23505":
                    raise IntegrityUniqueException("Invite key is not unique") from exc
                # SQLSTATE_FK_VIOLATION - some fields do not exist
                if sql_state == "23503":
                    raise IntegrityForeignException("Server or inviter fields are not found") from exc
                raise IntegrityUnknownException("Could not create invite") from exc

        for _ in range(5):
            candidate = await self._generate_key()
            values["key"] = candidate

            stmt = (
                insert(Invite)
                .values(**values)
                .on_conflict_do_nothing(index_elements=['key'])
                .returning(Invite)
            )
            try:
                result = await self.session.execute(stmt)
                invite = result.scalar_one_or_none()
            except IntegrityError as exc:
                sql_state = getattr(exc.orig, "sqlstate", None)
                # SQLSTATE_FK_VIOLATION - some fields do not exist
                if sql_state == "23503":
                    raise IntegrityForeignException("Server or inviter fields are not found") from exc
                raise IntegrityUnknownException("Could not create invite") from exc

            if invite is not None:
                return invite
        raise InviteUniqueException()

    async def set_use_limit(self, invite: Invite, use_limit: int) -> Invite:
        if use_limit < 0:
            use_limit = 0
        invite.use_limit = use_limit
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def decrement_use_limit(self, invite: Invite) -> Invite:
        if invite.use_limit > 0:
            invite.use_limit -= 1
            self.session.add(invite)
            await self.session.flush()
        return invite

    async def delete(self, invite_id: UUID) -> bool:
        stmt = delete(Invite).where(Invite.id == invite_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
