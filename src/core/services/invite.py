from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    InviteUniqueException,
    NotFoundException,
)
from src.core.interfaces.repo.invite import InviteRepositoryProtocol
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.invite import Invite, InviteCreate
from src.core.models.member import Member, MemberCreate, MemberUpdate
from src.infra.postgre.static import PERMISSION, RESTRICTION


class InviteService:
    def __init__(
            self,
            invite_repo: InviteRepositoryProtocol,
            server_repo: ServerRepositoryProtocol,
            member_repo: MemberRepositoryProtocol,
    ) -> None:
        self.invite_repo = invite_repo
        self.server_repo = server_repo
        self.member_repo = member_repo

    async def get_invite_info(self, key: str) -> Invite:
        invite_field = await self.invite_repo.get_by_key(key)
        if not invite_field:
            raise NotFoundException("Invite not found")
        return invite_field

    async def use_invite(self, key: str, user_id: UUID, nickname: str, restriction_mask: int = 0) -> Member:
        invite_field = await self.invite_repo.get_by_key(key)
        if not invite_field or invite_field.use_limit <= 0:
            raise NotFoundException("Invite not found")

        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException("Invite not found")

        server_field = await self.server_repo.get(invite_field.server_id)
        if server_field is None:
            raise InternalLogicException("Server not found")
        existing_member = await self.member_repo.get_by_user_in_server(server_field.id, user_id)
        if existing_member:
            if not existing_member.active:
                await self.member_repo.update(MemberUpdate(id=existing_member.id, active=True))
            member_field = existing_member
        else:
            try:
                member_field = await self.member_repo.create(
                    MemberCreate(server_id=server_field.id, user_id=user_id, nickname=nickname)
                )
            except IntegrityForeignException as exc:
                raise NotFoundException(exc.message)
            except IntegrityUnknownException as exc:
                raise InternalLogicException(exc.message)
            await self.invite_repo.decrement_use_limit(invite_field)
        return member_field

    async def list_invites(self, server_id: UUID, permission_mask: int = 0) -> list[Invite]:
        server_field = await self.server_repo.get(server_id)
        if not server_field:
            raise NotFoundException("Server not found")

        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to list invites")

        invites = await self.invite_repo.list_for_server(server_id)
        return list(invites)

    async def create_invite(
            self,
            server_id: UUID,
            use_limit: int | None,
            inviter_id: UUID | None,
            permission_mask: int = 0,
    ) -> Invite:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to create invite")

        use_limit = use_limit if use_limit is not None else 0
        use_limit = max(use_limit, 0)

        try:
            invite_field = await self.invite_repo.create(
                InviteCreate(server_id=server_id, use_limit=use_limit, inviter_id=inviter_id)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUnknownException, IntegrityUniqueException, InviteUniqueException) as exc:
            raise InternalLogicException(exc.message)
        return invite_field

    async def revoke_invite(self, server_id: UUID, invite_id: UUID, permission_mask: int = 0) -> None:
        invite_field = await self.invite_repo.get(invite_id)
        if not invite_field or invite_field.server_id != server_id:
            raise NotFoundException("Invite not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to revoke invite")

        ok = await self.invite_repo.delete(invite_id)
        if not ok:
            raise NotFoundException("Invite not found")
