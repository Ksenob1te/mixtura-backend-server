from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.server import Server as ServerDTO
from src.core.models.server import ServerCreate, ServerUpdate

from ..models import Member
from ..models import Server as ServerModel
from .base import BaseRepository


class ServerRepository(
    BaseRepository[ServerModel, ServerCreate, ServerDTO, ServerUpdate],
    ServerRepositoryProtocol,
):
    model = ServerModel
    dto_model = ServerDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    @staticmethod
    async def _apply_filter(
            stmt: Select,
            page: int | None = None,
            name_filter: str | None = None,
            page_size: int = 50,
    ) -> Select:
        if name_filter:
            stmt = stmt.where(ServerModel.name.ilike(f"%{name_filter}%"))
        if page is not None:
            current_page = max(1, page)
            stmt = stmt.limit(page_size).offset((current_page - 1) * page_size)
        return stmt

    async def list_public(
            self,
            page: int | None = None,
            name_filter: str | None = None,
            page_size: int = 50,
    ) -> Sequence[ServerDTO]:
        stmt = select(ServerModel).where(ServerModel.public.is_(True))
        stmt = await self._apply_filter(stmt, page, name_filter, page_size)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_by_owner(
            self,
            owner_id: UUID,
            page: int | None = None,
            name_filter: str = "",
            page_size: int = 50,
    ) -> Sequence[ServerDTO]:
        stmt = select(ServerModel).where(ServerModel.owner_id == owner_id)
        stmt = await self._apply_filter(stmt, page, name_filter, page_size)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_by_user(
            self,
            user_id: UUID,
            page: int | None = None,
            name_filter: str | None = None,
            page_size: int = 50,
    ) -> Sequence[ServerDTO]:
        stmt = select(ServerModel).where(
            ServerModel.members.any(
                (Member.user_id == user_id) &
                (Member.active == True)
            )
        )
        stmt = await self._apply_filter(stmt, page, name_filter, page_size)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]
