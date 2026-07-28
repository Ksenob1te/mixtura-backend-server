from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.custom import CustomRepositoryProtocol
from src.core.models.custom import Custom as CustomDTO
from src.core.models.custom import CustomCreate

from ..models import Custom as CustomModel
from .base import BaseRepository


class CustomRepository(
    BaseRepository[CustomModel, CustomCreate, CustomDTO, CustomDTO],
    CustomRepositoryProtocol,
):
    model = CustomModel
    dto_model = CustomDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_for_member(self, member_id: UUID) -> Sequence[CustomDTO]:
        stmt = select(CustomModel).where(CustomModel.member_id == member_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]
