import secrets
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InviteUniqueException,
)
from src.core.interfaces.repo.invite import InviteRepositoryProtocol
from src.core.models.invite import Invite as InviteDTO
from src.core.models.invite import InviteCreate

from ..models import Invite as InviteModel
from .base import BaseRepository


class InviteRepository(
    BaseRepository[InviteModel, InviteCreate, InviteDTO, InviteDTO],
    InviteRepositoryProtocol,
):
    model = InviteModel
    dto_model = InviteDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_key(self, key: str) -> InviteDTO | None:
        stmt = select(InviteModel).where(InviteModel.key == key).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def list_for_server(self, server_id: UUID) -> Sequence[InviteDTO]:
        stmt = select(InviteModel).where(InviteModel.server_id == server_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    @staticmethod
    async def _generate_key(length: int = 12) -> str:
        raw = secrets.token_urlsafe(length)
        return raw.replace('-', '').replace('_', '')[:length]

    async def create(self, dto: InviteCreate) -> InviteDTO:
        values: dict[str, str | int | UUID | None] = {
            "server_id": dto.server_id,
            "inviter_id": dto.inviter_id,
            "use_limit": dto.use_limit,
        }

        key = dto.key

        if key is not None:
            values["key"] = key
            stmt = (
                insert(InviteModel)
                .values(**values)
                .returning(InviteModel)
            )
            try:
                result = await self._session.execute(stmt)
                invite = result.scalar_one()
                await self._session.refresh(invite)
                return self._to_dto(invite)
            except IntegrityError as exc:
                sql_state = getattr(exc.orig, "sqlstate", None)
                if sql_state == "23505":
                    raise IntegrityUniqueException("Invite key is not unique") from exc
                if sql_state == "23503":
                    raise IntegrityForeignException("Server or inviter fields are not found") from exc
                raise IntegrityUnknownException("Could not create invite") from exc

        for _ in range(5):
            candidate = await self._generate_key()
            values["key"] = candidate

            stmt = (
                insert(InviteModel)
                .values(**values)
                .on_conflict_do_nothing(index_elements=['key'])
                .returning(InviteModel)
            )
            try:
                result = await self._session.execute(stmt)
                invite = result.scalar_one_or_none()
            except IntegrityError as exc:
                sql_state = getattr(exc.orig, "sqlstate", None)
                if sql_state == "23503":
                    raise IntegrityForeignException("Server or inviter fields are not found") from exc
                raise IntegrityUnknownException("Could not create invite") from exc

            if invite is not None:
                await self._session.refresh(invite)
                return self._to_dto(invite)
        raise InviteUniqueException()

    async def decrement_use_limit(self, invite: InviteDTO) -> InviteDTO:
        stmt = select(InviteModel).where(InviteModel.id == invite.id).limit(1)
        invite_model = await self._session.scalar(stmt)
        if invite_model is None:
            return invite
        if invite_model.use_limit > 0:
            invite_model.use_limit -= 1
            await self._flush()
        return self._to_dto(invite_model)
