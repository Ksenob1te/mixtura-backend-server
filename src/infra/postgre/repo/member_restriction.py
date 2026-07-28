from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.member_restriction import (
    MemberRestrictionRepositoryProtocol,
)
from src.core.models.member_restriction import MemberRestriction as MemberRestrictionDTO
from src.core.models.member_restriction import MemberRestrictionCreate

from ..models import MemberRestriction as MemberRestrictionModel
from .base import BaseRepository


class MemberRestrictionRepository(
    BaseRepository[MemberRestrictionModel, MemberRestrictionCreate, MemberRestrictionDTO, MemberRestrictionDTO],
    MemberRestrictionRepositoryProtocol,
):
    model = MemberRestrictionModel
    dto_model = MemberRestrictionDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_for_member(self, member_id: UUID) -> Sequence[MemberRestrictionDTO]:
        stmt = select(MemberRestrictionModel).where(MemberRestrictionModel.member_id == member_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_active_for_member(self, member_id: UUID, now: datetime | None = None) -> Sequence[MemberRestrictionDTO]:
        if now is None:
            now = datetime.now(UTC)
        stmt = select(MemberRestrictionModel).where(
            MemberRestrictionModel.member_id == member_id,
            MemberRestrictionModel.expiration_date > now
        )
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]
