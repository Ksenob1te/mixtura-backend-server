from uuid import UUID

from src.domain.exceptions import NotFoundException, MigrationException, InternalLogicException, ForbiddenException
from src.domain.models.member.request import (
    VirtualMemberCreateRequest,
    MemberUpdateRequest,
    MemberMigrationRequest,
)
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    ServerRoleRepository
)
from src.infra.postgre.models import Member
from src.infra.postgre.static import PERMISSION, RESTRICTION
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException


class MemberService:
    def __init__(
            self,
            member_repo: MemberRepository,
            server_repo: ServerRepository,
            server_role_repo: ServerRoleRepository,
    ):
        self.member_repo = member_repo
        self.server_repo = server_repo
        self.server_role_repo = server_role_repo

    async def list_members(
            self, server_id: UUID,
            page: int | None = None,
            nickname_filter: str = "",
            page_size: int = 50
    ) -> list[Member]:
        members = await self.member_repo.list_active_for_server(server_id, page, nickname_filter, page_size)
        return list(members)

    async def join_server(self, server_id: UUID, user_id: UUID, nickname: str, restriction_mask: int = 0) -> Member:
        server = await self.server_repo.get_by_id(server_id)
        if not server or not server.public:
            raise NotFoundException("Server not found")
        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException("Server not found")

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
            nickname: str,
            permission_mask: int = 0
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.CREATE_VIRTUAL):
            raise ForbiddenException("Unable to create virtual member")
        try:
            member_field = await self.member_repo.create(
                server_id=server_id,
                user_id=None,
                nickname=nickname,
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
            raise NotFoundException("Member with id not found")
        return member

    async def update_member(
            self,
            server_id: UUID,
            issuer_id: UUID,
            permission_mask: int,
            restriction_mask: int,
            member_id: UUID,
            name: str | None = None,
            server_role_id: UUID | None = None,
    ) -> Member:
        member = await self.member_repo.get_by_id(member_id)
        if member is None or member.server_id != server_id:
            raise NotFoundException("Member not found")
        if name and name != member.nickname:
            if issuer_id == member_id and RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SELF_EDIT_NAME):
                raise ForbiddenException("Unable to edit name")
            if issuer_id != member_id and not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_NAME):
                raise ForbiddenException("Unable to edit member name")
            member = await self.member_repo.set_nickname(member, name)

        if server_role_id is not None:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLES):
                raise ForbiddenException("Unable to assign role to member")

            assign_role = await self.server_role_repo.get_by_id(server_role_id)
            issuer_field = await self.member_repo.get_by_id(issuer_id)
            if not assign_role or not issuer_field or assign_role.server_id != server_id:
                raise NotFoundException("Server role not found")
            if (
                    assign_role.position >= issuer_field.server_role.position or
                    not issuer_field.server_role
            ):
                raise ForbiddenException("Unable to assign role to member")
            member = await self.member_repo.set_role(member, server_role_id)
        return member

    async def kick_member(self, issuer_id: UUID, server_id: UUID, member_id: UUID, permission_mask: int) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.KICK_MEMBERS) or issuer_id == member_id:
            raise ForbiddenException("Unable to kick member")
        member_field = await self.member_repo.get_by_id(member_id)
        issuer_field = await self.member_repo.get_by_id(issuer_id)
        if not member_field or not issuer_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        server_field = issuer_field.server
        if server_field is None:
            raise InternalLogicException("Member's server not found")
        if (
                server_field.owner_id == member_field.user_id or
                member_field.server_role and
                (
                        not issuer_field.server_role or
                        member_field.server_role.position >= issuer_field.server_role.position
                )
        ):
            raise ForbiddenException("Unable to kick member")
        await self.member_repo.deactivate(member_field)

    async def migrate_member(
            self,
            server_id: UUID,
            origin_member_id: UUID,
            target_member_id: UUID,
            permission_mask: int,
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.MIGRATE_MEMBERS):
            raise ForbiddenException("Unable to migrate member")
        current_member = await self.member_repo.get_by_id(origin_member_id)
        target_member = await self.member_repo.get_by_id(target_member_id)
        if (
                not target_member or not current_member or
                target_member.server_id != server_id or
                current_member.server_id != server_id
        ):
            raise NotFoundException("Member not found")
        user_id: UUID | None = current_member.user_id
        if user_id is None:
            raise MigrationException()
        await self.member_repo.remove_user(current_member)
        await self.member_repo.deactivate(current_member)
        success = await self.member_repo.set_user_if_none(target_member, user_id)
        if not success:
            raise MigrationException()
        return target_member
