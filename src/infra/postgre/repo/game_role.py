from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.game_role import GameRoleRepositoryProtocol
from src.core.models.game_role import GameRole as GameRoleDTO
from src.core.models.game_role import GameRoleCreate, GameRoleUpdate

from ..models import GameRole as GameRoleModel
from .base import BaseRepository


class GameRoleRepository(
    BaseRepository[GameRoleModel, GameRoleCreate, GameRoleDTO, GameRoleUpdate],
    GameRoleRepositoryProtocol,
):
    model = GameRoleModel
    dto_model = GameRoleDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_for_set(self, role_set_id: UUID) -> Sequence[GameRoleDTO]:
        stmt = select(GameRoleModel).where(GameRoleModel.role_set_id == role_set_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def copy_role(self, template_role: GameRoleDTO, new_role_set_id: UUID) -> GameRoleDTO:
        return await self.create(GameRoleCreate(
            name=template_role.name,
            role_set_id=new_role_set_id,
            min_in_team=template_role.min_in_team,
            max_in_team=template_role.max_in_team,
            icon_id=template_role.icon_id,
            hidden=template_role.hidden,
        ))
