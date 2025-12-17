from uuid import UUID
from datetime import datetime
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Restriction

from ..exceptions import IntegrityUnknownException, IntegrityUniqueException


class RestrictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, code_id: UUID) -> Restriction | None:
        stmt = select(Restriction).where(Restriction.id == code_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_code(self, code: str) -> Restriction | None:
        stmt = select(Restriction).where(Restriction.code == code).limit(1)
        return await self.session.scalar(stmt)

    async def list_all(self) -> Sequence[Restriction]:
        stmt = select(Restriction)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, code: str) -> Restriction:
        restriction_field = Restriction(code=code)
        try:
            self.session.add(restriction_field)
            await self.session.flush()
            restriction_field = await self.get_by_id(restriction_field.id)
            if restriction_field is None:
                raise IntegrityUnknownException("Failed to create restriction")
            return restriction_field
        except IntegrityError as exc:
            # SQLSTATE_UNIQUE_VIOLATION - restriction with this code already exists
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23505":
                raise IntegrityUniqueException("Restriction with this code already exists") from exc
            raise IntegrityUnknownException("Failed to create restriction") from exc

    async def delete(self, code_id: UUID) -> bool:
        stmt = delete(Restriction).where(Restriction.id == code_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def get_by_code_bulk(self, codes: Sequence[str]) -> Sequence[Restriction]:
        stmt = select(Restriction).where(Restriction.code.in_(codes))
        res = await self.session.scalars(stmt)
        return res.all()

