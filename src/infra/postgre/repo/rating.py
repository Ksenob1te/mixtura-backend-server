from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.rating import RatingRepositoryProtocol
from src.core.models.rating import Rating as RatingDTO
from src.core.models.rating import RatingCreate, RatingUpdate

from ..models import Rating as RatingModel
from .base import BaseRepository


class RatingRepository(
    BaseRepository[RatingModel, RatingCreate, RatingDTO, RatingUpdate],
    RatingRepositoryProtocol,
):
    model = RatingModel
    dto_model = RatingDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_for_set(self, rating_set_id: UUID) -> Sequence[RatingDTO]:
        stmt = select(RatingModel).where(RatingModel.rating_set_id == rating_set_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def copy_rating(self, rating: RatingDTO, new_rating_set_id: UUID) -> RatingDTO:
        return await self.create(RatingCreate(
            icon_id=rating.icon_id,
            threshold=rating.threshold,
            rating_set_id=new_rating_set_id,
        ))
