from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.rating import RatingRepositoryProtocol
from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.rating import Rating, RatingCreate, RatingUpdate
from src.core.models.rating_set import RatingSet, RatingSetUpdate
from src.infra.postgre.static import PERMISSION


class RatingService:
    def __init__(
            self,
            rating_repo: RatingRepositoryProtocol,
            rating_set_repo: RatingSetRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
    ) -> None:
        self.rating_repo = rating_repo
        self.rating_set_repo = rating_set_repo
        self.server_repo = server_repo

    async def get_rating_set(self, server_id: UUID) -> RatingSet:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        rating_set = await self.rating_set_repo.get_by_server_id(server_id)
        if rating_set is None:
            raise InternalLogicException("Rating set not found for server")
        return rating_set

    async def _check_rating_set(self, server_id: UUID, rating_set_id: UUID) -> RatingSet:
        rating_set_field = await self.rating_set_repo.get_by_server_id(server_id)
        if not rating_set_field or rating_set_field.id != rating_set_id:
            raise NotFoundException("Rating set not found for server")
        return rating_set_field

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

        update_data: dict = {}
        if name is not None and name != rating_set_field.name:
            update_data["name"] = name
        if min_rating is not None and min_rating != rating_set_field.min_rating:
            update_data["min_rating"] = min_rating
        if max_rating is not None and max_rating != rating_set_field.max_rating:
            update_data["max_rating"] = max_rating

        if update_data:
            rating_set_field = await self.rating_set_repo.update(RatingSetUpdate(id=rating_set_id, **update_data))
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
        await self._check_rating_set(server_id, rating_set_id)
        try:
            rating_field = await self.rating_repo.create(
                RatingCreate(icon_id=icon_id, threshold=threshold, rating_set_id=rating_set_id)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return rating_field

    async def _check_rating(self, server_id: UUID, rating_id: UUID) -> Rating:
        rating_field = await self.rating_repo.get(rating_id)
        if not rating_field:
            raise NotFoundException("Rating not found")
        rating_set_field = await self.rating_set_repo.get_by_server_id(server_id)
        if not rating_set_field or rating_set_field.id != rating_field.rating_set_id:
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

        update_data: dict = {}
        if threshold is not None and threshold != rating_field.threshold:
            update_data["threshold"] = threshold
        if icon_id is not None and icon_id != rating_field.icon_id:
            update_data["icon_id"] = icon_id

        if update_data:
            rating_field = await self.rating_repo.update(RatingUpdate(id=rating_id, **update_data))
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
        await self._check_rating(server_id, rating_id)
        rating_field = await self.rating_repo.update(RatingUpdate(id=rating_id, icon_id=None))
        return rating_field
