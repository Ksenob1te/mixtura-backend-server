from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.models.member import Member as MemberDTO
from src.core.models.member import MemberCreate, MemberUpdate

from ..models import Member as MemberModel
from .base import BaseRepository


class MemberRepository(
    BaseRepository[MemberModel, MemberCreate, MemberDTO, MemberUpdate],
    MemberRepositoryProtocol,
):
    model = MemberModel
    dto_model = MemberDTO

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_user_in_server(self, server_id: UUID, user_id: UUID) -> MemberDTO | None:
        stmt = select(MemberModel).where(MemberModel.server_id == server_id, MemberModel.user_id == user_id).limit(1)
        result = await self._session.scalar(stmt)
        return self._to_dto(result) if result else None

    async def list_for_server(self, server_id: UUID) -> Sequence[MemberDTO]:
        stmt = select(MemberModel).where(MemberModel.server_id == server_id)
        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def list_active_for_server(self, server_id: UUID, page: int | None = None,
                                     nickname_filter: str | None = None, page_size: int = 50) -> Sequence[MemberDTO]:
        stmt = select(MemberModel).where(MemberModel.server_id == server_id, MemberModel.active.is_(True))

        if nickname_filter:
            stmt = stmt.where(MemberModel.nickname.ilike(f"%{nickname_filter}%"))

        stmt = stmt.order_by(MemberModel.nickname)

        if page is not None:
            current_page = max(1, page)
            stmt = stmt.limit(page_size).offset((current_page - 1) * page_size)

        res = await self._session.scalars(stmt)
        return [self._to_dto(item) for item in res.all()]

    async def set_user_if_none(self, member: MemberDTO, user_id: UUID) -> bool:
        if member.user_id is not None:
            return False

        conflict_exists = select(MemberModel.id).where(
            MemberModel.server_id == member.server_id,
            MemberModel.user_id == user_id
        ).exists()

        stmt = (
            update(MemberModel)
            .where(MemberModel.id == member.id)
            .where(MemberModel.user_id.is_(None))
            .where(~conflict_exists)
            .values(user_id=user_id)
            .returning(MemberModel.id)
        )
        res = await self._session.execute(stmt)
        success = res.scalar_one_or_none() is not None
        if success:
            await self._flush()
            return True
        return False
