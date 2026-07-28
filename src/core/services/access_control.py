from datetime import datetime
from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.member_restriction import (
    MemberRestrictionRepositoryProtocol,
)
from src.core.interfaces.repo.permission import PermissionRepositoryProtocol
from src.core.interfaces.repo.restriction import RestrictionRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.interfaces.repo.server_role import ServerRoleRepositoryProtocol
from src.core.models.member import Member
from src.core.models.member_restriction import (
    MemberRestriction,
    MemberRestrictionCreate,
)
from src.core.models.permission import Permission
from src.core.models.server import Server
from src.infra.postgre.static import PERMISSION, RESTRICTION


class AccessControlService:
    def __init__(
            self,
            member_repo: MemberRepositoryProtocol,
            member_restriction_repo: MemberRestrictionRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
            restriction_repo: RestrictionRepositoryProtocol,
            permission_repo: PermissionRepositoryProtocol,
            server_role_repo: ServerRoleRepositoryProtocol,
    ):
        self.member_repo = member_repo
        self.member_restriction_repo = member_restriction_repo
        self.server_repo = server_repo
        self.restriction_repo = restriction_repo
        self.permission_repo = permission_repo
        self.server_role_repo = server_role_repo

    @staticmethod
    async def _transform_permissions_to_enum(permissions: list[Permission]) -> list[PERMISSION]:
        return [PERMISSION(p.code) for p in permissions]

    async def _transform_enum_to_permissions(self, permissions: list[PERMISSION]) -> list[Permission]:
        return list(await self.permission_repo.get_by_code_bulk(list(map(str, permissions))))

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
        server = await self.server_repo.get(server_id)
        if server is None:
            raise NotFoundException("Server not found")
        if member is None:
            if server.public:
                return None
            else:
                raise NotFoundException("Server not found")
        return member

    async def get_permissions(self, server_id: UUID, user_id: UUID) -> list[Permission]:
        member = await self.get_member(server_id, user_id)
        if member is None:
            return []
        server_field = await self.server_repo.get(member.server_id)
        if not server_field:
            raise InternalLogicException("Server for member not found")
        is_owner = server_field.owner_id == user_id
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = await self._transform_permissions_to_enum(list(permissions))
        permission_codes = await self._compute_overwrites_enum(permission_codes, is_owner)
        return await self._transform_enum_to_permissions(permission_codes)

    async def get_permission_mask(self, server_id: UUID, user_id: UUID) -> int:
        member = await self.get_member(server_id, user_id)
        if member is None:
            return 0
        server_field = await self.server_repo.get(member.server_id)
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
        restriction_enums = []
        for r in restrictions:
            restriction_obj = await self.restriction_repo.get(r.restriction_id)
            if restriction_obj is not None:
                restriction_enums.append(RESTRICTION(restriction_obj.code))
        restriction_mask = RESTRICTION.serialize_restriction_codes(restriction_enums)
        return restriction_mask

    async def _can_manipulate_restrictions(self, issuer_field: Member, member_field: Member, server_field: Server) -> None:
        can_manipulate_restriction: bool = False
        if (
                member_field.server_role_id is not None and
                issuer_field.server_role_id is not None
        ):
            issuer_role = await self.server_role_repo.get(issuer_field.server_role_id)
            member_role = await self.server_role_repo.get(member_field.server_role_id)
            if issuer_role is not None and member_role is not None and issuer_role.position > member_role.position:
                can_manipulate_restriction = True
        if member_field.server_role_id is None and issuer_field.server_role_id is not None:
            can_manipulate_restriction = True
        if server_field.owner_id == issuer_field.user_id:
            can_manipulate_restriction = True

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
        member_field = await self.member_repo.get(member_id)
        if not member_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        restriction_field = await self.restriction_repo.get(restriction_id)
        if not restriction_field:
            raise NotFoundException("Restriction not found")
        if not PERMISSION.check_permission(permission_mask, f"restrict_{restriction_field.code}"):
            raise ForbiddenException("Unable to add restriction")
        issuer_field = await self.member_repo.get(issuer_id)
        if issuer_field is None:
            raise InternalLogicException("Issuer member or role not found")
        server_field = await self.server_repo.get(issuer_field.server_id)
        if server_field is None:
            raise InternalLogicException("Server not found")
        await self._can_manipulate_restrictions(issuer_field, member_field, server_field)
        try:
            member_restriction_field = await self.member_restriction_repo.create(
                MemberRestrictionCreate(
                    member_id=member_id,
                    restriction_id=restriction_id,
                    reason=reason,
                    expiration_date=expiration_date,
                    creator_id=issuer_id,
                )
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
        issuer_field = await self.member_repo.get(issuer_id)
        if issuer_field is None:
            raise NotFoundException("Issuer member not found")
        member_restriction_field = await self.member_restriction_repo.get(member_restriction_id)
        if not member_restriction_field or member_restriction_field.member_id != member_id:
            raise NotFoundException("Member restriction not found")

        restriction_obj = await self.restriction_repo.get(member_restriction_field.restriction_id)
        if restriction_obj is None:
            raise InternalLogicException("Restriction not found")
        if not PERMISSION.check_permission(permission_mask, f"restrict_{restriction_obj.code}"):
            raise ForbiddenException("Unable to remove restriction")

        member_field = await self.member_repo.get(member_restriction_field.member_id)
        if member_field is None or member_field.server_id != server_id:
            raise InternalLogicException("Member not found")
        server_field = await self.server_repo.get(issuer_field.server_id)
        if server_field is None:
            raise InternalLogicException("Server not found")
        await self._can_manipulate_restrictions(issuer_field, member_field, server_field)

        status = await self.member_restriction_repo.delete(member_restriction_id)
        if not status:
            raise NotFoundException("Member restriction not found")
