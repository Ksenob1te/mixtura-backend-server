from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.custom_rating import CustomRatingRepositoryProtocol
from src.core.models.custom_rating import CustomRating as CustomRatingDTO
from src.core.models.custom_rating import CustomRatingCreate, CustomRatingUpdate

from ..models import CustomRating as CustomRatingModel
from .base import BaseRepository


class CustomRatingRepository(
    BaseRepository[CustomRatingModel, CustomRatingCreate, CustomRatingDTO, CustomRatingUpdate],
    CustomRatingRepositoryProtocol,
):
    model = CustomRatingModel
    dto_model = CustomRatingDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_custom_role(self, custom_id: UUID, game_role_id: UUID) -> CustomRatingDTO | None:
        stmt = select(CustomRatingModel).where(
            CustomRatingModel.custom_id == custom_id,
            CustomRatingModel.game_role_id == game_role_id
        ).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def list_for_custom(self, custom_id: UUID) -> Sequence[CustomRatingDTO]:
        stmt = select(CustomRatingModel).where(CustomRatingModel.custom_id == custom_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def delete_by_custom_rating(self, custom_id: UUID, game_role_id: UUID) -> bool:
        stmt = delete(CustomRatingModel).where(
            CustomRatingModel.custom_id == custom_id,
            CustomRatingModel.game_role_id == game_role_id
        )
        return bool(await self._execute_dml(stmt))
