from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.models.rating_set import RatingSet as RatingSetDTO
from src.core.models.rating_set import RatingSetCreate, RatingSetUpdate

from ..models import RatingSet as RatingSetModel
from .base import BaseRepository


class RatingSetRepository(
    BaseRepository[RatingSetModel, RatingSetCreate, RatingSetDTO, RatingSetUpdate],
    RatingSetRepositoryProtocol,
):
    model = RatingSetModel
    dto_model = RatingSetDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_name(self, name: str) -> RatingSetDTO | None:
        stmt = select(RatingSetModel).where(RatingSetModel.name == name).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_by_server_id(self, server_id: UUID) -> RatingSetDTO | None:
        stmt = select(RatingSetModel).where(RatingSetModel.server_id == server_id).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_global(self) -> Sequence[RatingSetDTO]:
        stmt = select(RatingSetModel).where(RatingSetModel.is_global.is_(True))
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def copy_global(self, global_rating_set: RatingSetDTO, server_id: UUID | None = None) -> RatingSetDTO:
        return await self.create(RatingSetCreate(
            name=global_rating_set.name,
            min_rating=global_rating_set.min_rating,
            max_rating=global_rating_set.max_rating,
            is_global=False,
            server_id=server_id,
        ))
