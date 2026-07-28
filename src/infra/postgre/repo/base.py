from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import CursorResult, Executable, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
)

from ..engine import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateDTO = TypeVar("CreateDTO", bound=BaseModel)
ReadDTO = TypeVar("ReadDTO", bound=BaseModel)
UpdateDTO = TypeVar("UpdateDTO", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateDTO, ReadDTO, UpdateDTO]):  # noqa: UP046
    model: type[ModelType]
    dto_model: type[ReadDTO]

    def __init__(self, session: AsyncSession):
        self._session = session
        if not hasattr(self, "model"):
            raise NotImplementedError("Repository must define 'model' class attribute")
        if not hasattr(self, "dto_model"):
            raise NotImplementedError("Repository must define 'dto_model' class attribute")

    async def _flush(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException() from exc
            if sql_state == "23505":
                raise IntegrityUniqueException() from exc
            raise IntegrityUnknownException() from exc

    async def _execute_dml(self, stmt: Executable) -> int:
        """Execute a DML statement, flush, and return the number of affected rows."""
        result = await self._session.execute(stmt)
        await self._flush()
        return cast(CursorResult[Any], result).rowcount

    async def _get_model(self, field_id: UUID, options: list[Any] | None = None) -> ModelType | None:
        stmt = select(self.model).where(getattr(self.model, "id") == field_id)  # noqa: B009
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalar(stmt)
        return result

    def _to_dto(self, obj: Any) -> ReadDTO:
        return self.dto_model.model_validate(obj, from_attributes=True)

    async def _get(self, field_id: UUID, options: list[Any] | None = None) -> ReadDTO | None:
        obj = await self._get_model(field_id, options=options)
        return self._to_dto(obj) if obj else None

    async def get(self, field_id: UUID) -> ReadDTO | None:
        return await self._get(field_id)

    async def _list_model(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        if options:
            stmt = stmt.options(*options)
        if order_by is not None:
            stmt = stmt.order_by(order_by)

        result = await self._session.scalars(stmt)
        return result.all()

    async def get_list(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ReadDTO]:
        items = await self._list_model(offset, limit, options, *where_clauses, order_by=order_by)
        return [self._to_dto(item) for item in items]

    def _dto_to_data(self, dto: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(dto, "model_dump"):
            raw_data = dto.model_dump(exclude_unset=exclude_unset)
        elif isinstance(dto, Mapping):
            raw_data = dict(dto)
        else:
            raw_data = dict(dto.__dict__)

        column_names = set(self.model.__mapper__.columns.keys())
        return {k: v for k, v in raw_data.items() if k in column_names}

    async def create(self, dto: CreateDTO) -> ReadDTO:
        create_data = self._dto_to_data(dto)
        obj = self.model(**create_data)
        self._session.add(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def update(self, dto: UpdateDTO) -> ReadDTO:
        update_data = self._dto_to_data(dto, exclude_unset=True)
        obj = self.model(**update_data)
        obj = await self._session.merge(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def delete(self, field_id: UUID) -> bool:
        obj = await self._get_model(field_id)
        if obj:
            await self._session.delete(obj)
            await self._flush()
            return True
        return False

    async def exists(self, field_id: UUID) -> bool:
        stmt = select(func.count()).select_from(self.model).where(getattr(self.model, "id") == field_id)  # noqa: B009
        count = await self._session.scalar(stmt)
        return (count or 0) > 0

    async def count(self, *where_clauses: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        val = await self._session.scalar(stmt)
        return val or 0
