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

    async def update_rating_set(
            self, rating_set_id: UUID, body: RatingSetUpdateRequest, permission_mask: int = 0
    ) -> RatingSet:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_set = await self.rating_set_repo.get_by_id(rating_set_id)
        if not rating_set:
            raise NotFoundException("Rating set not found")

        if body.name is not None and body.name != rating_set.name:
            rating_set = await self.rating_set_repo.set_name(rating_set, body.name)

        if body.min_rating is not None and body.min_rating != rating_set.min_rating:
            rating_set = await self.rating_set_repo.set_min_rating(
                rating_set, body.min_rating
            )

        if body.max_rating is not None and body.max_rating != rating_set.max_rating:
            rating_set = await self.rating_set_repo.set_max_rating(
                rating_set, body.max_rating
            )

        return rating_set

    async def create_rating(
            self,
            rating_set_id: UUID,
            body: RatingItemCreateRequest,
            icon_url: str,
            icon_id: UUID,
            permission_mask: int = 0
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")

        rating_set = await self.rating_set_repo.get_by_id(rating_set_id)
        if not rating_set:
            raise NotFoundException("Rating set not found")
        try:
            rating = await self.rating_repo.create(
                icon_url=icon_url,
                icon_id=icon_id,
                threshold=body.threshold,
                rating_set_id=rating_set_id,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        rating_set.ratings = rating_set.ratings + [rating]
        return rating

    async def update_rating(
            self,
            rating_id: UUID,
            body: RatingItemUpdateRequest,
            permission_mask: int = 0
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating = await self.rating_repo.get_by_id(rating_id)
        if not rating:
            raise NotFoundException("Rating not found")
        if body.threshold is not None and body.threshold != rating.threshold:
            rating = await self.rating_repo.set_threshold(rating, body.threshold)
        return rating

    async def delete_rating(self, rating_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        status = await self.rating_repo.delete(rating_id)
        if not status:
            raise NotFoundException("Rating not found")

    # async def update_rating_icon(
    #         self,
    #         rating_id: UUID,
    #         icon_url: str,
    #         icon_id: UUID,
    # ) -> Rating:
    #     rating = await self.rating_repo.get_by_id(rating_id)
    #     if not rating:
    #         raise NotFoundException("Rating not found")
    #     rating = await self.rating_repo.set_icon(rating, icon_url, icon_id)
    #     return rating
