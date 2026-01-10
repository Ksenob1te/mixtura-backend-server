from uuid import UUID
from datetime import datetime

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.domain.models.member.request import AddMemberRestrictionRequest
from src.infra.postgre.repo import (
    MemberRepository,
    MemberRestrictionRepository,
    ServerRepository,
    RestrictionRepository,
    PermissionRepository,
)
from src.infra.postgre.models import Member, MemberRestriction, Permission, Server
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

    @staticmethod
    async def _transform_permissions_to_enum(permissions: list[Permission]) -> list[PERMISSION]:
        return [PERMISSION(p.code) for p in permissions]

    @staticmethod
    async def _transform_permission_to_mask(permissions: list[Permission]) -> int:
        permission_codes = [PERMISSION(p.code) for p in permissions]
        permission_mask = PERMISSION.serialize_permission_codes(permission_codes)
        return permission_mask

    @staticmethod
    async def _compute_overwrites_enum(permissions: list[PERMISSION], is_owner: bool = False) -> list[PERMISSION]:
        if PERMISSION.ADMINISTRATOR in permissions or is_owner:
            return [p for p in PERMISSION]
        return permissions

    @staticmethod
    async def _compute_overwrites_mask(permission_mask: int, is_owner: bool = False) -> int:
        if PERMISSION.check_permission(permission_mask, PERMISSION.ADMINISTRATOR) or is_owner:
            return (1 << len(PERMISSION)) - 1
        return permission_mask

    async def get_member(self, server_id: UUID, user_id: UUID) -> Member | None:
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

    async def get_permissions(self, server_id: UUID, user_id: UUID) -> list[PERMISSION]:
        member = await self.get_member(server_id, user_id)
        if member is None:
            return []
        server_field = member.server
        if not server_field:
            raise InternalLogicException("Server for member not found")
        is_owner = server_field.owner_id == user_id
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = await self._transform_permissions_to_enum(list(permissions))
        permission_codes = await self._compute_overwrites_enum(permission_codes, is_owner)
        return permission_codes

    async def get_permission_mask(self, server_id: UUID, user_id: UUID) -> int:
        member = await self.get_member(server_id, user_id)
        if member is None:
            return 0
        server_field = member.server
        if not server_field:
            raise InternalLogicException("Server for member not found")
        is_owner = server_field.owner_id == user_id
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = await self._transform_permission_to_mask(list(permissions))
        return await self._compute_overwrites_mask(permission_codes, is_owner)

    async def get_restrictions(self, server_id: UUID, user_id: UUID) -> list[MemberRestriction]:
        try:
            member = await self.get_member(server_id, user_id)
        except NotFoundException:
            return []
        if member is None:
            return []
        restrictions = await self.member_restriction_repo.list_for_member(member.id)
        return list(restrictions)

    async def get_restriction_mask(self, server_id: UUID, user_id: UUID) -> int:
        member = await self.get_member(server_id, user_id)
        if member is None:
            return 0
        restrictions = await self.member_restriction_repo.list_for_member(member.id)
        restriction_enum = [RESTRICTION(r.restriction.code) for r in restrictions]
        restriction_mask = RESTRICTION.serialize_restriction_codes(restriction_enum)
        return restriction_mask

    @staticmethod
    async def _can_manipulate_restrictions(issuer_field: Member, member_field: Member, server_field: Server) -> None:
        can_manipulate_restriction: bool = False
        if (
                member_field.server_role is not None and
                issuer_field.server_role is not None and
                issuer_field.server_role.position > member_field.server_role.position
        ):
            can_manipulate_restriction = True
        if member_field.server_role is None and issuer_field.server_role is not None:
            can_manipulate_restriction = True
        if server_field.owner_id == issuer_field.user_id:
            can_manipulate_restriction = True

        # overwrite flag if member is owner
        if server_field.owner_id == member_field.user_id:
            can_manipulate_restriction = False

        if not can_manipulate_restriction:
            raise ForbiddenException("Unable to add restriction")

    async def add_restriction(self, member_id: UUID,
                              issuer_id: UUID,
                              server_id: UUID,
                              permission_mask: int,
                              reason: str,
                              expiration_date: datetime,
                              restriction_id: UUID) -> MemberRestriction:
        member_field = await self.member_repo.get_by_id(member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException(f"Member not found")
        restriction_field = await self.restriction_repo.get_by_id(restriction_id)
        if not restriction_field:
            raise NotFoundException(f"Restriction not found")
        if not PERMISSION.check_permission(permission_mask, f"restrict_{restriction_field.code}"):
            raise ForbiddenException("Unable to add restriction")
        issuer_field = await self.member_repo.get_by_id(issuer_id)
        if issuer_field is None:
            raise InternalLogicException("Issuer member or role not found")
        server_field = issuer_field.server
        if server_field is None:
            raise InternalLogicException("Server not found")
        await self._can_manipulate_restrictions(issuer_field, member_field, server_field)
        try:
            member_restriction_field = await self.member_restriction_repo.create(
                member_id=member_id,
                restriction_id=restriction_id,
                reason=reason,
                expiration_date=expiration_date,
                creator_id=issuer_id,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return member_restriction_field

    async def remove_restriction(self, member_id: UUID,
                                 issuer_id: UUID,
                                 server_id: UUID,
                                 member_restriction_id: UUID,
                                 permission_mask: int = 0) -> None:
        issuer_field = await self.member_repo.get_by_id(issuer_id)
        if issuer_field is None:
            raise NotFoundException(f"Issuer member not found")
        member_restriction_field = await self.member_restriction_repo.get_by_id(member_restriction_id)
        if not member_restriction_field or member_restriction_field.member_id != member_id:
            raise NotFoundException(f"Member restriction not found")
        if not PERMISSION.check_permission(
                permission_mask,
                f"restrict_{member_restriction_field.restriction.code}"  # type: ignore
        ):
            raise ForbiddenException("Unable to remove restriction")

        member_field = member_restriction_field.member
        if member_field is None or member_field.server_id != server_id:
            raise InternalLogicException(f"Member not found")
        server_field = issuer_field.server
        if server_field is None:
            raise InternalLogicException("Server not found")
        await self._can_manipulate_restrictions(issuer_field, member_field, server_field)

        status = await self.member_restriction_repo.delete(member_restriction_id)
        if not status:
            raise NotFoundException(f"Member restriction not found")
