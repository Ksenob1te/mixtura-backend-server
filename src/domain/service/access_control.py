from uuid import UUID

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.domain.models.member.request import AddMemberRestrictionRequest
from src.infra.postgre.repo import (
    MemberRepository,
    MemberRestrictionRepository,
    ServerRepository,
    RestrictionRepository,
    PermissionRepository
)
from src.infra.postgre.models import Member, MemberRestriction, Permission
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException


class AccessControlService:
    def __init__(
            self,
            member_repo: MemberRepository,
            member_restriction_repo: MemberRestrictionRepository,
            server_repo: ServerRepository,
            restriction_repo: RestrictionRepository,
            permission_repo: PermissionRepository,
    ):
        self.member_repo = member_repo
        self.member_restriction_repo = member_restriction_repo
        self.server_repo = server_repo
        self.restriction_repo = restriction_repo
        self.permission_repo = permission_repo

    async def _get_member(self, server_id: UUID, user_id: UUID) -> Member | None:
        member = await self.member_repo.get_by_user_in_server(server_id, user_id)
        server = await self.server_repo.get_by_id(server_id)
        if server is None:
            raise NotFoundException(f"Server not found")
        if member is None:
            if server.public:
                return None
            else:
                raise NotFoundException(f"Server not found")
        return member

    async def get_permissions(self, server_id: UUID, user_id: UUID) -> list[str]:
        member = await self._get_member(server_id, user_id)
        # TODO: for server owner get all permissions
        if member is None:
            return []
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = [p.code for p in permissions]
        return permission_codes

    @staticmethod
    async def _compute_base_permissions(permissions: list[Permission]) -> int:
        permission_codes = [PERMISSION(p.code) for p in permissions]
        permission_mask = PERMISSION.serialize_permission_codes(permission_codes)
        return permission_mask

    @staticmethod
    async def _compute_overwrites(permission_mask: int) -> int:
        if PERMISSION.check_permission(permission_mask, PERMISSION.ADMINISTRATOR):
            return (1 << len(PERMISSION)) - 1
        return permission_mask

    async def get_permission_mask(self, server_id: UUID, user_id: UUID) -> int:
        member = await self._get_member(server_id, user_id)
        if member is None:
            return 0
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = await self._compute_base_permissions(list(permissions))
        return await self._compute_overwrites(permission_codes)

    async def get_restrictions(self, server_id: UUID, user_id: UUID) -> list[MemberRestriction]:
        member = await self._get_member(server_id, user_id)
        if member is None:
            return []
        restrictions = await self.member_restriction_repo.list_for_member(member.id)
        return list(restrictions)

    async def get_restriction_mask(self, server_id: UUID, user_id: UUID) -> int:
        member = await self._get_member(server_id, user_id)
        if member is None:
            return 0
        restrictions = await self.member_restriction_repo.list_for_member(member.id)
        restriction_enum = [RESTRICTION(r.restriction.code) for r in restrictions]
        restriction_mask = RESTRICTION.serialize_restriction_codes(restriction_enum)
        return restriction_mask

    async def add_restriction(self, member_id: UUID,
                              issuer_id: UUID,
                              body: AddMemberRestrictionRequest, # TODO: replacy body
                              permission_mask: int = 0) -> MemberRestriction:
       # TODO: check if belongs to issuer member server
        restriction_field = await self.restriction_repo.get_by_id(body.restriction_id)
        if not restriction_field:
            raise NotFoundException(f"Restriction not found")
        if not PERMISSION.check_permission(permission_mask, f"restrict_{restriction_field.code}"):
            # TODO: discuss about this dynamic permission check
            raise ForbiddenException("Unable to add restriction")
        # TODO: compare issuer with target
        try:
            member_restriction_field = await self.member_restriction_repo.create(
                member_id=member_id,
                restriction_id=body.restriction_id,
                reason=body.reason,
                expiration_date=body.expiration_date,
                creator_id=issuer_id,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return member_restriction_field

    async def remove_restriction(self, member_id: UUID,
                                 member_restriction_id: UUID,
                                 permission_mask: int = 0) -> None:
        # TODO: check if belongs to issuer member server
        member_restriction_field = await self.member_restriction_repo.get_by_id(member_restriction_id)
        if not member_restriction_field or member_restriction_field.member_id != member_id:
            raise NotFoundException(f"Member restriction not found")
        if not PERMISSION.check_permission(
                permission_mask,
                f"restrict_{member_restriction_field.restriction.code}"  # type: ignore
        ):
            raise ForbiddenException("Unable to remove restriction")
        status = await self.member_restriction_repo.delete(member_restriction_id)
        if not status:
            raise NotFoundException(f"Member restriction not found")
