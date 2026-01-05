from uuid import UUID

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.domain.models.rating.request import (
    RatingItemCreateRequest,
    RatingItemUpdateRequest,
    RatingSetUpdateRequest,
)
from src.infra.postgre.models import Rating, RatingSet
from src.infra.postgre.repo import RatingRepository, RatingSetRepository, ServerRepository

from src.infra.postgre.static import PERMISSION
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException


class RatingService:
    def __init__(
            self,
            rating_repo: RatingRepository,
            rating_set_repo: RatingSetRepository,
            server_repo: ServerRepository,
    ) -> None:
        self.rating_repo = rating_repo
        self.rating_set_repo = rating_set_repo
        self.server_repo = server_repo

    async def get_rating_set(self, server_id: UUID) -> RatingSet:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server.rating_set

    async def _check_rating_set(self, server_id: UUID, rating_set_id: UUID) -> RatingSet:
        server_field = await self.server_repo.get_by_id(server_id)
        if not server_field or server_field.rating_set_id != rating_set_id:
            raise NotFoundException("Rating set not found for server")
        return server_field.rating_set

    async def update_rating_set(
            self, server_id: UUID,
            rating_set_id: UUID,
            name: str | None = None,
            min_rating: int | None = None,
            max_rating: int | None = None,
            permission_mask: int = 0
    ) -> RatingSet:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_set_field = await self._check_rating_set(server_id, rating_set_id)
        if name is not None and name != rating_set_field.name:
            rating_set_field = await self.rating_set_repo.set_name(rating_set_field, name)

        if min_rating is not None and min_rating != rating_set_field.min_rating:
            rating_set_field = await self.rating_set_repo.set_min_rating(
                rating_set_field, min_rating
            )

        if max_rating is not None and max_rating != rating_set_field.max_rating:
            rating_set_field = await self.rating_set_repo.set_max_rating(
                rating_set_field, max_rating
            )

        return rating_set_field

    async def create_rating(
            self,
            server_id: UUID,
            rating_set_id: UUID,
            threshold: int,
            icon_id: UUID | None = None,
            permission_mask: int = 0
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_set_field = await self._check_rating_set(server_id, rating_set_id)
        try:
            rating_field = await self.rating_repo.create(
                icon_id=icon_id,
                threshold=threshold,
                rating_set_id=rating_set_id,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        rating_set_field.ratings = rating_set_field.ratings + [rating_field]
        return rating_field

    async def _check_rating(self, server_id, rating_id) -> Rating:
        rating_field = await self.rating_repo.get_by_id(rating_id)
        if not rating_field:
            raise NotFoundException("Rating not found")
        server_field = await self.server_repo.get_by_id(server_id)
        if not server_field or server_field.rating_set_id != rating_field.rating_set_id:
            raise NotFoundException("Rating not found for server")
        return rating_field

    async def update_rating(
            self,
            server_id: UUID,
            rating_id: UUID,
            threshold: int | None = None,
            icon_id: UUID | None = None,
            permission_mask: int = 0
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_field = await self._check_rating(server_id, rating_id)
        if threshold is not None and threshold != rating_field.threshold:
            rating_field = await self.rating_repo.set_threshold(rating_field, threshold)
        if icon_id is not None and icon_id != rating_field.icon_id:
            rating_field = await self.rating_repo.set_icon(rating_field, icon_id)
        return rating_field

    async def delete_rating(self, server_id: UUID, rating_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        await self._check_rating(server_id, rating_id)
        status = await self.rating_repo.delete(rating_id)
        if not status:
            raise NotFoundException("Rating not found")

    async def delete_rating_icon(
            self,
            server_id: UUID,
            rating_id: UUID,
            permission_mask: int = 0
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_field = await self._check_rating(server_id, rating_id)
        rating_field = await self.rating_repo.set_icon(rating_field, None)
        return rating_field
