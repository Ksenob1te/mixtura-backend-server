from uuid import UUID

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException, BadRequestException
from src.infra.postgre.models import Custom
from src.infra.postgre.repo import (
    CustomRepository,
    CustomRatingRepository,
    MemberRepository,
    GameRoleRepository,
)
from src.infra.postgre.static import PERMISSION
from src.infra.postgre import (
    IntegrityUniqueException,
    IntegrityForeignException,
    IntegrityUnknownException
)


class MemberCustomService:
    def __init__(
            self,
            custom_repo: CustomRepository,
            custom_rating_repo: CustomRatingRepository,
            member_repo: MemberRepository,
            game_role_repo: GameRoleRepository,
    ) -> None:
        self.custom_repo = custom_repo
        self.custom_rating_repo = custom_rating_repo
        self.member_repo = member_repo
        self.game_role_repo = game_role_repo

    async def list_customs(self, server_id: UUID, member_id: UUID) -> list[Custom]:
        member_field = await self.member_repo.get_by_id(member_id)
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
        member_field = await self.member_repo.get_by_id(member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        try:
            custom = await self.custom_repo.create(member_id=member_id, creator_id=issuer_id)
        except IntegrityForeignException:
            raise NotFoundException("Issuer field not found")
        except IntegrityUnknownException:
            raise InternalLogicException("Failed to create custom")
        return custom

    async def get_custom(self, server_id: UUID, custom_id: UUID) -> Custom:
        custom = await self.custom_repo.get_by_id(custom_id)
        if custom and not custom.member:
            raise InternalLogicException("Member for custom not found")
        if not custom or not custom.member.server_id == server_id:
            raise NotFoundException("Custom not found")
        return custom

    async def delete_custom(self, server_id: UUID, custom_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.DELETE_CUSTOM):
            raise ForbiddenException("Unable to delete custom")
        # raises Internal and NotFound exceptions if needed
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
        server_field = custom.member.server
        if server_field is None:
            raise InternalLogicException("Server for member not found")
        rating_set_field = server_field.rating_set
        if rating_set_field is None:
            raise InternalLogicException("Rating set for server not found")
        if rating_set_field.min_rating > rating or rating > rating_set_field.max_rating:
            raise BadRequestException("Rating value is out of bounds")
        custom_rating_field = await self.custom_rating_repo.get_by_custom_role(custom_id, game_role_id)
        if custom_rating_field is None:
            try:
                custom_rating_field = await self.custom_rating_repo.create(custom_id, game_role_id, rating)
            except IntegrityForeignException as exc:
                raise NotFoundException(exc.message)
            except IntegrityUniqueException as exc:
                raise InternalLogicException(exc.message)
            except IntegrityUnknownException as exc:
                raise InternalLogicException(exc.message)
            custom.custom_ratings = custom.custom_ratings + [custom_rating_field]
        else:
            await self.custom_rating_repo.set_rating(custom_rating_field, rating)
        return custom
