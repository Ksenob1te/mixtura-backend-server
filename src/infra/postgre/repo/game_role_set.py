from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.game_role_set import GameRoleSetRepositoryProtocol
from src.core.models.game_role_set import GameRoleSet as GameRoleSetDTO
from src.core.models.game_role_set import (
    GameRoleSetCreate,
    GameRoleSetDetail,
    GameRoleSetUpdate,
)

from ..models import GameRoleSet as GameRoleSetModel
from .base import BaseRepository


class GameRoleSetRepository(
    BaseRepository[GameRoleSetModel, GameRoleSetCreate, GameRoleSetDTO, GameRoleSetUpdate],
    GameRoleSetRepositoryProtocol,
):
    model = GameRoleSetModel
    dto_model = GameRoleSetDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    @staticmethod
    def _to_detail_dto(obj: GameRoleSetModel) -> GameRoleSetDetail:
        return GameRoleSetDetail.model_validate(obj, from_attributes=True)

    async def get_by_game_id(self, game_id: UUID) -> GameRoleSetDTO | None:
        stmt = select(GameRoleSetModel).where(GameRoleSetModel.game_id == game_id).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_detail(self, role_set_id: UUID) -> GameRoleSetDetail | None:
        obj = await self._get_model(role_set_id)
        return self._to_detail_dto(obj) if obj else None
