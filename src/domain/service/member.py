from uuid import UUID

from src.domain.exceptions import NotFoundException, MigrationException, InternalLogicException, ForbiddenException
from src.domain.models.member.request import (
    VirtualMemberCreateRequest,
    MemberUpdateRequest,
    MigrationRequest,
    MemberRestrictionCreateRequest
)
from src.infra.postgre.repo import MemberRepository, MemberRestrictionRepository, ServerRepository, \
    ServerRoleRepository, RestrictionRepository, PermissionRepository
from src.infra.postgre.models import Member, MemberRestriction, Permission
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException


class MemberService:
    def __init__(
            self,
            member_repo: MemberRepository,
            member_restriction_repo: MemberRestrictionRepository,
            server_repo: ServerRepository,
            server_role_repo: ServerRoleRepository,
            restriction_repo: RestrictionRepository,
            permission_repo: PermissionRepository,
    ):
        self.member_repo = member_repo
        self.member_restriction_repo = member_restriction_repo
        self.server_repo = server_repo
        self.server_role_repo = server_role_repo
        self.restriction_repo = restriction_repo
        self.permission_repo = permission_repo

    async def list_members(self, server_id: UUID) -> list[Member]:
        members = await self.member_repo.list_active_for_server(server_id)
        return list(members)

    async def join_server(self, server_id: UUID, user_id: UUID, nickname: str, restriction_mask: int = 0) -> Member:
        server = await self.server_repo.get_by_id(server_id)
        if not server or not server.public:
            raise NotFoundException(f"Server not found")
        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException(f"Server not found")

        existing_member = await self.member_repo.get_by_user_in_server(server_id, user_id)
        if existing_member:
            if not existing_member.active:
                await self.member_repo.activate(existing_member)
            return existing_member
        try:
            member_field = await self.member_repo.create(
                server_id=server_id,
                user_id=user_id,
                nickname=nickname,
                server_role_id=None
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUnknownException, IntegrityUniqueException) as exc:
            raise InternalLogicException(exc.message)
        return member_field

    async def create_virtual(
            self,
            server_id: UUID,
            body: VirtualMemberCreateRequest,
            permission_mask: int = 0
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.CREATE_VIRTUAL):
            raise ForbiddenException("Unable to create virtual member")
        try:
            member_field = await self.member_repo.create(
                server_id=server_id,
                user_id=None,
                nickname=body.nickname,
                server_role_id=None
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return member_field

    async def get_member(self, member_id: UUID) -> Member:
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id not found")
        return member

    async def update_member(
            self,
            issuer_id: UUID,
            member_id: UUID,
            body: MemberUpdateRequest,
            permission_mask: int,
            restriction_mask: int
    ) -> Member:
        member = await self.member_repo.get_by_id(member_id)
        if member is None:
            raise NotFoundException(f"Member not found")
        # мне все еще не нравится что-то тут, возможно все-таки нужно право на редактирование самого себя
        if body.name and body.name != member.nickname:
            if issuer_id == member_id and RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SELF_EDIT_NAME):
                raise ForbiddenException("Unable to edit name")
            if issuer_id != member_id and not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_NAME):
                raise ForbiddenException("Unable to edit member name")
            member = await self.member_repo.set_nickname(member, body.name)

        if body.server_role_id is not None:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLES):
                raise ForbiddenException("Unable to assign role to member")

            assign_role = await self.server_role_repo.get_by_id(body.server_role_id)
            issuer_field = await self.member_repo.get_by_id(issuer_id)
            if not assign_role or not issuer_field or not issuer_field.server_role:
                raise NotFoundException(f"Server role not found")
            if assign_role.position >= issuer_field.server_role.position:  # type: ignore
                raise ForbiddenException("Unable to assign role to member")
            member = await self.member_repo.set_role(member, body.server_role_id)
        return member

    async def kick_member(self, member_id: UUID, permission_mask: int) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.KICK_MEMBERS):
            raise ForbiddenException("Unable to kick member")
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member not found")
        await self.member_repo.deactivate(member)

    async def migrate_member(
            self,
            member_id: UUID,
            body: MigrationRequest,
            permission_mask: int
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.MIGRATE_MEMBERS):
            raise ForbiddenException("Unable to migrate member")
        current_member = await self.member_repo.get_by_id(member_id)
        target_member = await self.member_repo.get_by_id(body.target_member_id)
        if not target_member or not current_member:
            raise NotFoundException(f"Member not found")
        user_id: UUID | None = current_member.user_id  # type: ignore
        if user_id is None:
            raise MigrationException()
        await self.member_repo.remove_user(current_member)
        await self.member_repo.deactivate(current_member)
        success = await self.member_repo.set_user_if_none(target_member, user_id)
        if not success:
            raise MigrationException()
        return target_member

    async def get_permissions(self, member_id: UUID) -> list[str]:
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id not found")
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

    async def get_permission_mask(self, member_id: UUID) -> int:
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id not found")
        permissions = await self.permission_repo.list_for_role(member.server_role_id)
        permission_codes = await self._compute_base_permissions(list(permissions))
        return await self._compute_overwrites(permission_codes)

    async def get_restrictions(self, member_id: UUID) -> list[MemberRestriction]:
        restrictions = await self.member_restriction_repo.list_for_member(member_id)
        return list(restrictions)

    async def get_restriction_mask(self, member_id: UUID) -> int:
        restrictions = await self.member_restriction_repo.list_for_member(member_id)
        restriction_enum = [RESTRICTION(r.restriction.code) for r in restrictions]
        restriction_mask = RESTRICTION.serialize_restriction_codes(restriction_enum)
        return restriction_mask

    async def add_restriction(self, member_id: UUID,
                              issuer_id: UUID,
                              body: MemberRestrictionCreateRequest,
                              permission_mask: int = 0) -> MemberRestriction:
        restriction_field = await self.restriction_repo.get_by_id(body.restriction_id)
        if not restriction_field:
            raise NotFoundException(f"Restriction not found")
        if not PERMISSION.check_permission(permission_mask, f"restrict_{restriction_field.code}"):
            # TODO: discuss about this dynamic permission check
            raise ForbiddenException("Unable to add restriction")
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
