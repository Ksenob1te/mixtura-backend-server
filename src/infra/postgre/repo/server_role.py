from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.server_role import ServerRoleRepositoryProtocol
from src.core.models.server_role import ServerRole as ServerRoleDTO
from src.core.models.server_role import ServerRoleCreate, ServerRoleUpdate

from ..models import ServerRole as ServerRoleModel
from .base import BaseRepository


class ServerRoleRepository(
    BaseRepository[ServerRoleModel, ServerRoleCreate, ServerRoleDTO, ServerRoleUpdate],
    ServerRoleRepositoryProtocol,
):
    model = ServerRoleModel
    dto_model = ServerRoleDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_for_server(self, server_id: UUID) -> Sequence[ServerRoleDTO]:
        stmt = select(ServerRoleModel).where(ServerRoleModel.server_id == server_id).order_by(ServerRoleModel.position.asc())
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]
