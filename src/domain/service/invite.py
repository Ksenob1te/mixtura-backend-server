from uuid import UUID

from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.domain.models.invites.request import InviteCreateRequest
from src.infra.postgre.models import Invite, Member
from src.infra.postgre.repo import InviteRepository, ServerRepository, MemberRepository
from src.infra.postgre.static import RESTRICTION, PERMISSION

from sqlalchemy.exc import IntegrityError


class InviteService:
    def __init__(
        self,
        invite_repo: InviteRepository,
        server_repo: ServerRepository,
        member_repo: MemberRepository,
    ) -> None:
        self.invite_repo = invite_repo
        self.server_repo = server_repo
        self.member_repo = member_repo

    async def get_invite_info(self, key: str) -> Invite:
        invite = await self.invite_repo.get_by_key(key)
        if not invite:
            raise NotFoundException("Invite not found")
        return invite

    async def use_invite(self, key: str, user_id: UUID, username: str, restriction_mask: int = 0) -> Member:
        invite = await self.invite_repo.get_by_key(key)
        if not invite or invite.use_limit <= 0:
            raise NotFoundException("Invite not found")

        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException("Invite not found")

        server = invite.server
        existing_member = await self.member_repo.get_by_user_in_server(server.id, user_id)      # type: ignore
        if existing_member:
            if not existing_member.active:
                await self.member_repo.activate(existing_member)
            member = existing_member
        else:
            try:
                member = await self.member_repo.create(
                    server_id=server.id,        # type: ignore
                    user_id=user_id,
                    name=username,
                    server_role_id=None,
                )
            except Exception:
                raise InternalLogicException("Failed to join server via invite")
            if member is None:
                raise InternalLogicException("Failed to create member via invite")

        await self.invite_repo.decrement_use_limit(invite)
        return member

    async def list_invites(self, server_id: UUID, permission_mask: int = 0) -> list[Invite]:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")

        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to list invites")

        invites = await self.invite_repo.list_for_server(server_id)
        return list(invites)

    async def create_invite(
        self,
        server_id: UUID,
        body: InviteCreateRequest,
        inviter_id: UUID | None,
        permission_mask: int = 0,
    ) -> Invite:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to create invite")

        use_limit = body.use_limit if body.use_limit is not None else 0
        if use_limit < 0:
            use_limit = 0

        try:
            invite = await self.invite_repo.create(
                server_id=server_id,
                use_limit=use_limit,
                inviter_id=inviter_id,
            )
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some fields do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise NotFoundException("Some foreign fields are not found")
            raise InternalLogicException("Failed to create invite")
        if invite is None:
            raise InternalLogicException("Failed to create invite")

        return invite

    async def revoke_invite(self, invite_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES):
            raise ForbiddenException("Unable to revoke invite")

        ok = await self.invite_repo.delete(invite_id)
        if not ok:
            raise NotFoundException("Invite not found")
