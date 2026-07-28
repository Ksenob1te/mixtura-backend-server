from uuid import UUID

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.custom import CustomRepositoryProtocol
from src.core.interfaces.repo.custom_rating import CustomRatingRepositoryProtocol
from src.core.interfaces.repo.game_role import GameRoleRepositoryProtocol
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.rating_set import RatingSetRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.custom import Custom, CustomCreate
from src.core.models.custom_rating import CustomRatingCreate, CustomRatingUpdate
from src.infra.postgre.static import PERMISSION


class MemberCustomService:
    def __init__(
            self,
            custom_repo: CustomRepositoryProtocol,
            custom_rating_repo: CustomRatingRepositoryProtocol,
            member_repo: MemberRepositoryProtocol,
            game_role_repo: GameRoleRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
            rating_set_repo: RatingSetRepositoryProtocol,
    ) -> None:
        self.custom_repo = custom_repo
        self.custom_rating_repo = custom_rating_repo
        self.member_repo = member_repo
        self.game_role_repo = game_role_repo
        self.server_repo = server_repo
        self.rating_set_repo = rating_set_repo

    async def list_customs(self, server_id: UUID, member_id: UUID) -> list[Custom]:
        member_field = await self.member_repo.get(member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        customs = await self.custom_repo.list_for_member(member_id)
        return list(customs)

    async def create_custom(
            self, issuer_id: UUID, server_id: UUID,
            member_id: UUID, permission_mask: int = 0
    ) -> Custom:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.CREATE_CUSTOM):
            raise ForbiddenException("Unable to create custom")
        member_field = await self.member_repo.get(member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        try:
            custom = await self.custom_repo.create(CustomCreate(member_id=member_id, creator_id=issuer_id))
        except IntegrityForeignException:
            raise NotFoundException("Issuer field not found")
        except IntegrityUnknownException:
            raise InternalLogicException("Failed to create custom")
        return custom

    async def get_custom(self, server_id: UUID, custom_id: UUID) -> Custom:
        custom = await self.custom_repo.get(custom_id)
        if not custom:
            raise NotFoundException("Custom not found")
        member_field = await self.member_repo.get(custom.member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException("Custom not found")
        return custom

    async def delete_custom(self, server_id: UUID, custom_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.DELETE_CUSTOM):
            raise ForbiddenException("Unable to delete custom")
        await self.get_custom(server_id, custom_id)
        ok = await self.custom_repo.delete(custom_id)
        if not ok:
            raise NotFoundException("Custom not found")

    async def set_rating_value(
            self,
            issuer_id: UUID,
            server_id: UUID,
            custom_id: UUID,
            game_role_id: UUID,
            rating: int,
            permission_mask: int = 0,
    ) -> Custom:
        custom = await self.get_custom(server_id=server_id, custom_id=custom_id)
        if (
                custom.creator_id != issuer_id and
                not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ALL_CUSTOMS)
        ):
            raise ForbiddenException("Unable to change custom rating")

        member_field = await self.member_repo.get(custom.member_id)
        if member_field is None:
            raise InternalLogicException("Member for custom not found")
        server_field = await self.server_repo.get(member_field.server_id)
        if server_field is None:
            raise InternalLogicException("Server for member not found")
        rating_set_field = await self.rating_set_repo.get_by_server_id(server_field.id)
        if rating_set_field is None:
            raise InternalLogicException("Rating set for server not found")

        if rating_set_field.min_rating > rating or rating > rating_set_field.max_rating:
            raise BadRequestException("Rating value is out of bounds")
        custom_rating_field = await self.custom_rating_repo.get_by_custom_role(custom_id, game_role_id)
        if custom_rating_field is None:
            try:
                custom_rating_field = await self.custom_rating_repo.create(
                    CustomRatingCreate(custom_id=custom_id, game_role_id=game_role_id, rating=rating)
                )
            except IntegrityForeignException as exc:
                raise NotFoundException(exc.message)
            except IntegrityUniqueException as exc:
                raise InternalLogicException(exc.message)
            except IntegrityUnknownException as exc:
                raise InternalLogicException(exc.message)
        else:
            await self.custom_rating_repo.update(CustomRatingUpdate(id=custom_rating_field.id, rating=rating))
        return custom
