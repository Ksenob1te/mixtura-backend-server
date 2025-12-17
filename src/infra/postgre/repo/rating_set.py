from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import RatingSet
from sqlalchemy.exc import IntegrityError
from ..exceptions import IntegrityUnknownException, IntegrityUniqueException, IntegrityForeignException


class RatingSetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, rating_set_id: UUID) -> RatingSet | None:
        stmt = select(RatingSet).where(RatingSet.id == rating_set_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_name(self, name: str) -> RatingSet | None:
        stmt = select(RatingSet).where(RatingSet.name == name).limit(1)
        return await self.session.scalar(stmt)

    async def get_global(self) -> Sequence[RatingSet]:
        stmt = select(RatingSet).where(RatingSet.is_global.is_(True))
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, name: str, min_rating: int, max_rating: int, is_global: bool = False) -> RatingSet:
        if min_rating > max_rating:
            min_rating = max_rating
        rating_set_field = RatingSet(name=name, min_rating=min_rating, max_rating=max_rating, is_global=is_global)
        try:
            self.session.add(rating_set_field)
            await self.session.flush()
            rating_set_field = await self.get_by_id(rating_set_field.id)
            if rating_set_field is None:
                raise IntegrityUnknownException("Failed to create rating set")
            return rating_set_field
        except IntegrityError as exc:
            raise IntegrityUnknownException("Failed to create rating set") from exc

    async def set_name(self, rating_set: RatingSet, name: str) -> RatingSet:
        rating_set.name = name
        await self.session.flush()
        return rating_set

    async def set_min_rating(self, rating_set: RatingSet, min_rating: int) -> RatingSet:
        rating_set.min_rating = min_rating
        if rating_set.max_rating < min_rating:
            rating_set.min_rating = rating_set.max_rating
        await self.session.flush()
        return rating_set

    async def set_max_rating(self, rating_set: RatingSet, max_rating: int) -> RatingSet:
        rating_set.max_rating = max_rating
        if rating_set.min_rating > max_rating:
            rating_set.max_rating = rating_set.min_rating
        await self.session.flush()
        return rating_set

    async def set_global(self, rating_set: RatingSet, is_global: bool) -> RatingSet:
        rating_set.is_global = is_global
        await self.session.flush()
        return rating_set

    async def delete(self, rating_set_id: UUID) -> bool:
        stmt = delete(RatingSet).where(RatingSet.id == rating_set_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def copy_global(self, global_rating_set: RatingSet) -> RatingSet:
        return await self.create(
            name=global_rating_set.name,
            min_rating=global_rating_set.min_rating,
            max_rating=global_rating_set.max_rating,
            is_global=False
        )
