from uuid import UUID
from typing import Sequence
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import CustomRating
from ..exceptions import IntegrityForeignException, IntegrityUnknownException, IntegrityUniqueException
from sqlalchemy.exc import IntegrityError


class CustomRatingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, custom_rating_id: UUID) -> CustomRating | None:
        stmt = select(CustomRating).where(CustomRating.id == custom_rating_id).limit(1)
        return await self.session.scalar(stmt)

    async def get_by_custom_role(self, custom_id: UUID, game_role_id: UUID) -> CustomRating | None:
        stmt = select(CustomRating).where(
            CustomRating.custom_id == custom_id,
            CustomRating.game_role_id == game_role_id
        ).limit(1)
        return await self.session.scalar(stmt)

    async def list_for_custom(self, custom_id: UUID) -> Sequence[CustomRating]:
        stmt = select(CustomRating).where(CustomRating.custom_id == custom_id)
        res = await self.session.scalars(stmt)
        return res.all()

    async def create(self, custom_id: UUID, game_role_id: UUID, rating: int) -> CustomRating:
        custom_rating_field = CustomRating(custom_id=custom_id, game_role_id=game_role_id, rating=rating)
        try:
            self.session.add(custom_rating_field)
            await self.session.flush()
            custom_rating_field = await self.get_by_id(custom_rating_field.id)
            if custom_rating_field is None:
                raise IntegrityUnknownException("Failed to create custom rating")
            return custom_rating_field
        except IntegrityError as exc:
            # SQLSTATE_UNIQUE_VIOLATION - duplicate entry
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23505":
                raise IntegrityUniqueException("Custom rating for this custom and game role already exists")
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            if sql_state == "23503":
                raise IntegrityForeignException("Custom or game role fields are not found")
            raise IntegrityUnknownException("Failed to create custom rating")

    async def set_rating(self, custom_rating: CustomRating, rating: int) -> CustomRating:
        custom_rating.rating = rating
        await self.session.flush()
        return custom_rating

    async def delete(self, custom_rating_id: UUID) -> bool:
        stmt = delete(CustomRating).where(CustomRating.id == custom_rating_id)
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore

    async def delete_by_custom_rating(self, custom_id: UUID, game_role_id: UUID) -> bool:
        stmt = delete(CustomRating).where(
            CustomRating.custom_id == custom_id,
            CustomRating.game_role_id == game_role_id
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return bool(res.rowcount)  # type: ignore
