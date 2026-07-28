from uuid import UUID

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.game import GameRepositoryProtocol
from src.core.interfaces.repo.rating import RatingRepositoryProtocol
from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.game import Game
from src.core.models.rating import Rating, RatingCreate, RatingUpdate
from src.core.models.rating_set import RatingSet, RatingSetDetail, RatingSetUpdate
from src.infra.postgre.static import PERMISSION


class RatingService:
    def __init__(
            self,
            rating_repo: RatingRepositoryProtocol,
            rating_set_repo: RatingSetRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
            game_repo: GameRepositoryProtocol,
    ) -> None:
        self.rating_repo = rating_repo
        self.rating_set_repo = rating_set_repo
        self.server_repo = server_repo
        self.game_repo = game_repo

    async def _set_and_game(self, rating_set_id: UUID) -> tuple[RatingSet, Game]:
        rating_set = await self.rating_set_repo.get(rating_set_id)
        if rating_set is None:
            raise NotFoundException("Rating set not found")
        game = await self.game_repo.get(rating_set.game_id)
        if game is None:
            raise InternalLogicException("Game for rating set not found")
        return rating_set, game

    async def _require_local_set(self, server_id: UUID, rating_set_id: UUID) -> RatingSet:
        rating_set, game = await self._set_and_game(rating_set_id)
        if game.server_id is None:
            raise ForbiddenException("Unable to edit a global game rating set")
        if game.server_id != server_id:
            raise NotFoundException("Rating set not found for server")
        return rating_set

    async def _require_global_set(self, rating_set_id: UUID) -> RatingSet:
        rating_set, game = await self._set_and_game(rating_set_id)
        if game.server_id is not None:
            raise ForbiddenException("Rating set does not belong to a global game")
        return rating_set

    async def _require_local_rating(self, server_id: UUID, rating_id: UUID) -> Rating:
        rating = await self.rating_repo.get(rating_id)
        if rating is None:
            raise NotFoundException("Rating not found")
        await self._require_local_set(server_id, rating.rating_set_id)
        return rating

    async def _require_global_rating(self, rating_id: UUID) -> Rating:
        rating = await self.rating_repo.get(rating_id)
        if rating is None:
            raise NotFoundException("Rating not found")
        await self._require_global_set(rating.rating_set_id)
        return rating

    @staticmethod
    def _build_rating_set_update_data(
            current: RatingSet,
            name: str | None,
            min_rating: int | None,
            max_rating: int | None,
    ) -> dict:
        update_data: dict = {}
        if name is not None and name != current.name:
            update_data["name"] = name
        if min_rating is not None and min_rating != current.min_rating:
            update_data["min_rating"] = min_rating
        if max_rating is not None and max_rating != current.max_rating:
            update_data["max_rating"] = max_rating
        return update_data

    @staticmethod
    def _assert_bounds_valid(update_data: dict, current: RatingSet) -> None:
        eff_min = update_data.get("min_rating", current.min_rating)
        eff_max = update_data.get("max_rating", current.max_rating)
        if eff_min > eff_max:
            raise BadRequestException("Rating bounds are invalid")

    async def _apply_rating_set_update(
            self,
            rating_set_id: UUID,
            current: RatingSet,
            name: str | None,
            min_rating: int | None,
            max_rating: int | None,
    ) -> RatingSetDetail:
        update_data = self._build_rating_set_update_data(current, name, min_rating, max_rating)
        self._assert_bounds_valid(update_data, current)
        if update_data:
            await self.rating_set_repo.update(RatingSetUpdate(id=rating_set_id, **update_data))
        rating_set_detail = await self.rating_set_repo.get_detail(rating_set_id)
        if rating_set_detail is None:
            raise InternalLogicException("Rating set not found")
        return rating_set_detail

    async def update_rating_set(
            self,
            server_id: UUID,
            rating_set_id: UUID,
            name: str | None = None,
            min_rating: int | None = None,
            max_rating: int | None = None,
            permission_mask: int = 0,
    ) -> RatingSetDetail:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_set_field = await self._require_local_set(server_id, rating_set_id)
        return await self._apply_rating_set_update(rating_set_id, rating_set_field, name, min_rating, max_rating)

    async def update_global_rating_set(
            self,
            rating_set_id: UUID,
            name: str | None = None,
            min_rating: int | None = None,
            max_rating: int | None = None,
    ) -> RatingSetDetail:
        rating_set_field = await self._require_global_set(rating_set_id)
        return await self._apply_rating_set_update(rating_set_id, rating_set_field, name, min_rating, max_rating)

    async def _create_rating(self, rating_set_id: UUID, threshold: int, icon_id: UUID | None) -> Rating:
        try:
            rating_field = await self.rating_repo.create(
                RatingCreate(icon_id=icon_id, threshold=threshold, rating_set_id=rating_set_id)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return rating_field

    async def create_rating(
            self,
            server_id: UUID,
            rating_set_id: UUID,
            threshold: int,
            icon_id: UUID | None = None,
            permission_mask: int = 0,
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        await self._require_local_set(server_id, rating_set_id)
        return await self._create_rating(rating_set_id, threshold, icon_id)

    async def create_global_rating(self, rating_set_id: UUID, threshold: int, icon_id: UUID | None = None) -> Rating:
        await self._require_global_set(rating_set_id)
        return await self._create_rating(rating_set_id, threshold, icon_id)

    async def _apply_rating_update(
            self, rating: Rating, threshold: int | None = None, icon_id: UUID | None = None
    ) -> Rating:
        update_data: dict = {}
        if threshold is not None and threshold != rating.threshold:
            update_data["threshold"] = threshold
        if icon_id is not None and icon_id != rating.icon_id:
            update_data["icon_id"] = icon_id

        if update_data:
            rating = await self.rating_repo.update(RatingUpdate(id=rating.id, **update_data))
        return rating

    async def update_rating(
            self,
            server_id: UUID,
            rating_id: UUID,
            threshold: int | None = None,
            icon_id: UUID | None = None,
            permission_mask: int = 0,
    ) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_field = await self._require_local_rating(server_id, rating_id)
        return await self._apply_rating_update(rating_field, threshold, icon_id)

    async def update_global_rating(
            self, rating_id: UUID, threshold: int | None = None, icon_id: UUID | None = None
    ) -> Rating:
        rating_field = await self._require_global_rating(rating_id)
        return await self._apply_rating_update(rating_field, threshold, icon_id)

    async def delete_rating(self, server_id: UUID, rating_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        await self._require_local_rating(server_id, rating_id)
        status = await self.rating_repo.delete(rating_id)
        if not status:
            raise NotFoundException("Rating not found")

    async def delete_global_rating(self, rating_id: UUID) -> None:
        await self._require_global_rating(rating_id)
        status = await self.rating_repo.delete(rating_id)
        if not status:
            raise NotFoundException("Rating not found")

    async def delete_rating_icon(self, server_id: UUID, rating_id: UUID, permission_mask: int = 0) -> Rating:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_RATING_SET):
            raise ForbiddenException("Unable to edit rating set")
        rating_field = await self._require_local_rating(server_id, rating_id)
        return await self.rating_repo.update(RatingUpdate(id=rating_field.id, icon_id=None))

    async def delete_global_rating_icon(self, rating_id: UUID) -> Rating:
        rating_field = await self._require_global_rating(rating_id)
        return await self.rating_repo.update(RatingUpdate(id=rating_field.id, icon_id=None))
