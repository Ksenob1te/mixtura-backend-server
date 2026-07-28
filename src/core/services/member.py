from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    MigrationException,
    NotFoundException,
)
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.interfaces.repo.server_role import ServerRoleRepositoryProtocol
from src.core.models.member import Member, MemberCreate, MemberUpdate
from src.core.models.server import Server
from src.core.models.server_role import ServerRole
from src.infra.postgre.static import PERMISSION, RESTRICTION


class MemberService:
    def __init__(
            self,
            member_repo: MemberRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
            server_role_repo: ServerRoleRepositoryProtocol,
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
        server = await self.server_repo.get(server_id)
        if not server or not server.public:
            raise NotFoundException("Server not found")
        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException("Server not found")

        existing_member = await self.member_repo.get_by_user_in_server(server_id, user_id)
        if existing_member:
            if not existing_member.active:
                await self.member_repo.update(MemberUpdate(id=existing_member.id, active=True))
            return existing_member
        try:
            member_field = await self.member_repo.create(
                MemberCreate(server_id=server_id, user_id=user_id, nickname=nickname)
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
                MemberCreate(server_id=server_id, user_id=None, nickname=nickname)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return member_field

    async def get_member(self, member_id: UUID) -> Member:
        member = await self.member_repo.get(member_id)
        if not member:
            raise NotFoundException("Member with id not found")
        return member

    async def _can_manipulate_roles(self, issuer_field: Member, assign_role: ServerRole, server_field: Server) -> None:
        can_manipulate_roles: bool = False
        if issuer_field.server_role_id is not None:
            issuer_role = await self.server_role_repo.get(issuer_field.server_role_id)
            if issuer_role is not None and issuer_role.position > assign_role.position:
                can_manipulate_roles = True
        if server_field.owner_id == issuer_field.user_id:
            can_manipulate_roles = True

        if not can_manipulate_roles:
            raise ForbiddenException("Unable to assign role to member")

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
        member = await self.member_repo.get(member_id)
        if member is None or member.server_id != server_id:
            raise NotFoundException("Member not found")
        if name and name != member.nickname:
            if issuer_id == member_id and RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SELF_EDIT_NAME):
                raise ForbiddenException("Unable to edit name")
            if issuer_id != member_id and not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_NAME):
                raise ForbiddenException("Unable to edit member name")
            member = await self.member_repo.update(MemberUpdate(id=member.id, nickname=name))

        if server_role_id is not None:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLES):
                raise ForbiddenException("Unable to assign role to member")

            assign_role = await self.server_role_repo.get(server_role_id)
            issuer_field = await self.member_repo.get(issuer_id)
            if not assign_role or assign_role.server_id != server_id:
                raise NotFoundException("Server role not found")
            if not issuer_field:
                raise NotFoundException("Issuer not found")
            server_field = await self.server_repo.get(issuer_field.server_id)
            if not server_field:
                raise InternalLogicException("Server not found")
            await self._can_manipulate_roles(issuer_field, assign_role, server_field)
            member = await self.member_repo.update(MemberUpdate(id=member.id, server_role_id=server_role_id))
        return member

    async def kick_member(self, issuer_id: UUID, server_id: UUID, member_id: UUID, permission_mask: int) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.KICK_MEMBERS) or issuer_id == member_id:
            raise ForbiddenException("Unable to kick member")
        member_field = await self.member_repo.get(member_id)
        issuer_field = await self.member_repo.get(issuer_id)
        if not member_field or not issuer_field or member_field.server_id != server_id:
            raise NotFoundException("Member not found")
        server_field = await self.server_repo.get(issuer_field.server_id)
        if server_field is None:
            raise InternalLogicException("Member's server not found")

        assign_role = None
        if member_field.server_role_id is not None:
            assign_role = await self.server_role_repo.get(member_field.server_role_id)
        issuer_role = None
        if issuer_field.server_role_id is not None:
            issuer_role = await self.server_role_repo.get(issuer_field.server_role_id)

        if (
                server_field.owner_id == member_field.user_id or
                assign_role is not None and
                (
                        issuer_role is None or
                        assign_role.position >= issuer_role.position
                )
        ):
            raise ForbiddenException("Unable to kick member")
        await self.member_repo.update(MemberUpdate(id=member_field.id, active=False))

    async def migrate_member(
            self,
            server_id: UUID,
            origin_member_id: UUID,
            target_member_id: UUID,
            permission_mask: int,
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.MIGRATE_MEMBERS):
            raise ForbiddenException("Unable to migrate member")
        current_member = await self.member_repo.get(origin_member_id)
        target_member = await self.member_repo.get(target_member_id)
        if (
                not target_member or not current_member or
                target_member.server_id != server_id or
                current_member.server_id != server_id
        ):
            raise NotFoundException("Member not found")
        user_id: UUID | None = current_member.user_id
        if user_id is None:
            raise MigrationException()
        await self.member_repo.update(MemberUpdate(id=current_member.id, user_id=None))
        await self.member_repo.update(MemberUpdate(id=current_member.id, active=False))
        success = await self.member_repo.set_user_if_none(target_member, user_id)
        if not success:
            raise MigrationException()
        return target_member
