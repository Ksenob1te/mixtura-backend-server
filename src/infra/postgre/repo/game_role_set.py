from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.game_role_set import GameRoleSetRepositoryProtocol
from src.core.models.game_role_set import GameRoleSet as GameRoleSetDTO
from src.core.models.game_role_set import GameRoleSetCreate, GameRoleSetUpdate

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

    async def get_by_name(self, name: str) -> GameRoleSetDTO | None:
        stmt = select(GameRoleSetModel).where(GameRoleSetModel.name == name).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_by_server_id(self, server_id: UUID) -> GameRoleSetDTO | None:
        stmt = select(GameRoleSetModel).where(GameRoleSetModel.server_id == server_id).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def get_global(self) -> Sequence[GameRoleSetDTO]:
        stmt = select(GameRoleSetModel).where(GameRoleSetModel.is_global.is_(True))
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def copy_global(self, global_role_set: GameRoleSetDTO, server_id: UUID | None = None) -> GameRoleSetDTO:
        return await self.create(GameRoleSetCreate(
            name=global_role_set.name,
            is_global=False,
            server_id=server_id,
        ))
