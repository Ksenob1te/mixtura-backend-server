from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.models.rating_set import RatingSet as RatingSetDTO
from src.core.models.rating_set import RatingSetCreate, RatingSetDetail, RatingSetUpdate

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

    @staticmethod
    def _to_detail_dto(obj: RatingSetModel) -> RatingSetDetail:
        return RatingSetDetail.model_validate(obj, from_attributes=True)

    async def get_by_game_id(self, game_id: UUID) -> RatingSetDTO | None:
        stmt = select(RatingSetModel).where(RatingSetModel.game_id == game_id).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_detail(self, rating_set_id: UUID) -> RatingSetDetail | None:
        obj = await self._get_model(rating_set_id)
        return self._to_detail_dto(obj) if obj else None
