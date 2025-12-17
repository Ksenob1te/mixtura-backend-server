from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Rating
from sqlalchemy.exc import IntegrityError

from ..exceptions import IntegrityForeignException, IntegrityUnknownException


class RatingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, rating_id: UUID) -> Rating | None:
        stmt = select(Rating).where(Rating.id == rating_id).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_set(self, rating_set_id: UUID) -> Sequence[Rating]:
        stmt = select(Rating).where(Rating.rating_set_id == rating_set_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, icon_url: str, icon_id: UUID, threshold: int, rating_set_id: UUID) -> Rating:
        rating = Rating(icon_url=icon_url, icon_id=icon_id, threshold=threshold, rating_set_id=rating_set_id)
        try:
            self.session.add(rating)
            await self.session.flush()
            rating_field = await self.get_by_id(rating.id)
            if rating_field is None:
                raise IntegrityUnknownException("Failed to create rating")
            return rating_field
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            if sql_state == "23503":
                raise IntegrityForeignException("Rating set field is not found") from exc
            raise IntegrityUnknownException("Failed to create rating") from exc

    async def set_icon(self, rating: Rating, icon_url: str, icon_id: UUID) -> Rating:
        rating.icon_url = icon_url
        rating.icon_id = icon_id
        self.session.add(rating)
        await self.session.flush()
        return rating

    async def set_threshold(self, rating: Rating, threshold: int) -> Rating:
        rating.threshold = threshold
        self.session.add(rating)
        await self.session.flush()
        return rating

    async def delete(self, rating_id: UUID) -> bool:
        stmt = delete(Rating).where(Rating.id == rating_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
