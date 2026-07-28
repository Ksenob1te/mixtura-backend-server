from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.restriction import RestrictionRepositoryProtocol
from src.core.models.restriction import Restriction as RestrictionDTO
from src.core.models.restriction import RestrictionCreate

from ..models import Restriction as RestrictionModel
from .base import BaseRepository


class RestrictionRepository(
    BaseRepository[RestrictionModel, RestrictionCreate, RestrictionDTO, RestrictionDTO],
    RestrictionRepositoryProtocol,
):
    model = RestrictionModel
    dto_model = RestrictionDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_code(self, code: str) -> RestrictionDTO | None:
        stmt = select(RestrictionModel).where(RestrictionModel.code == code).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_by_code_bulk(self, codes: Sequence[str]) -> Sequence[RestrictionDTO]:
        stmt = select(RestrictionModel).where(RestrictionModel.code.in_(codes))
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_all(self) -> Sequence[RestrictionDTO]:
        stmt = select(RestrictionModel)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]
