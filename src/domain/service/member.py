from uuid import UUID
from typing import Sequence
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from src.domain.exceptions import NotFoundException, MigrationException, InternalLogicException, ForbiddenException
from src.domain.models.member.request import (
    VirtualMemberCreateRequest,
    MemberUpdateRequest,
    MigrationRequest,
    MemberRestrictionCreateRequest
)
from src.domain.models.member.response import (
    MemberResponse,
    MemberRestrictionResponse,
    RestrictionResponse,
    ServerRoleResponse,
    ServerPermissionResponse
)
from src.domain.models.response import StatusResponse
from src.infra.postgre.repo.member import MemberRepository
from src.infra.postgre.repo.member_restriction import MemberRestrictionRepository
from src.infra.postgre.repo.server import ServerRepository
from src.infra.postgre.repo.server_role import ServerRoleRepository
from src.infra.postgre.repo.restriction import RestrictionRepository
from src.infra.postgre.models import Member, MemberRestriction

from src.infra.postgre.static import PERMISSION, RESTRICTION


class MemberService:
    def __init__(
            self,
            member_repo: MemberRepository,
            member_restriction_repo: MemberRestrictionRepository,
            server_repo: ServerRepository,
            server_role_repo: ServerRoleRepository,
            restriction_repo: RestrictionRepository,
    ):
        self.member_repo = member_repo
        self.member_restriction_repo = member_restriction_repo
        self.server_repo = server_repo
        self.server_role_repo = server_role_repo
        self.restriction_repo = restriction_repo

    # async def get_member_or_none(self, server_id: UUID, user_id: UUID,
    #                              ) -> Member | None:
    #     return await self.member_repo.get_by_user_in_server(server_id, user_id)

    async def list_members(self, server_id: UUID, permission_mask: int = 0) -> list[Member]:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.LIST_MEMBERS):
            raise NotFoundException(f"Server {server_id} not found")
        members = await self.member_repo.list_active_for_server(server_id)
        return list(members)

    async def join_server(self, server_id: UUID, user_id: UUID, name: str, restriction_mask: int = 0) -> Member:
        server = await self.server_repo.get_by_id(server_id)
        if not server or not server.public:
            raise NotFoundException(f"Server {server_id} not found")
        if RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN):
            raise NotFoundException(f"Server {server_id} not found")

        existing_member = await self.member_repo.get_by_user_in_server(server_id, user_id)
        if existing_member:
            if not existing_member.active:
                await self.member_repo.activate(existing_member)
            return existing_member
        try:
            member_field = await self.member_repo.create(
                server_id=server_id,
                user_id=user_id,
                name=name,
                server_role_id=None
            )
        except IntegrityError:
            raise InternalLogicException("Failed to join server due to integrity error")
        if member_field is None:
            raise InternalLogicException("Failed to create member")
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
                name=body.name,
                server_role_id=None
            )
        except IntegrityError:
            raise InternalLogicException("Failed to create virtual member due to integrity error")
        if member_field is None:
            raise InternalLogicException("Failed to create virtual member")
        return member_field

    async def get_member(self, member_id: UUID, permission_mask: int) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.LIST_MEMBERS):
            raise NotFoundException(f"Member with id {member_id} not found")
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id {member_id} not found")
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
            raise NotFoundException(f"Member with id {member_id} not found")

        if body.name and body.name != member.name:
            if PERMISSION.check_permission(
                    permission_mask, PERMISSION.SELF_EDIT
            ) and RESTRICTION.check_restriction(
                    restriction_mask, RESTRICTION.SELF_EDIT
            ):
                raise ForbiddenException("Unable to edit member name")
            if not PERMISSION.check_permission_bulk(
                    permission_mask,
                    [PERMISSION.SELF_EDIT, PERMISSION.EDIT_MEMBERS],
                    any
            ):
                raise ForbiddenException("Unable to edit member name")
            member = await self.member_repo.set_name(member, body.name)

        if body.server_role_id is not None:
            if not PERMISSION.check_permission(
                    permission_mask, PERMISSION.EDIT_MEMBERS
            ):
                raise ForbiddenException("Unable to assign role to member")

            assign_role = await self.server_role_repo.get_by_id(body.server_role_id)
            issuer_field = await self.member_repo.get_by_id(issuer_id)
            if not assign_role or not issuer_field.server_role:
                raise NotFoundException(f"Server role not found")
            if assign_role.position >= issuer_field.server_role.position:   # type: ignore
                raise ForbiddenException("Unable to assign role to member")
            member = await self.member_repo.set_role(member, body.server_role_id)
        return member

    async def kick_member(self, member_id: UUID, permission_mask: int) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.KICK_MEMBERS):
            raise ForbiddenException("Unable to kick member")
        member = await self.member_repo.get_by_id(member_id)
        await self.member_repo.deactivate(member)

    async def migrate_member(
        self,
        member_id: UUID,
        body: MigrationRequest,
        permission_mask: int
    ) -> Member:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.MIGRATE_MEMBERS):
            raise ForbiddenException("Unable to migrate member")
        member = await self.member_repo.get_by_id(member_id)
        if not member:
            raise NotFoundException(f"Member with id {member_id} not found")

        target_member = await self.member_repo.get_by_id(body.target_member_id)
        if target_member:
            if not target_member.active:
                await self.member_repo.activate(target_member)
            return target_member

        try:
            migrated_member = await self.member_repo.create(
                server_id=body.target_server_id,
                user_id=body.user_id,
                name=member.name,
                server_role_id=None
            )
        except IntegrityError:
            raise MigrationException("Failed to migrate member due to integrity error")
        if migrated_member is None:
            raise MigrationException("Failed to migrate member")
        return migrated_member


    #
    # async def get_restrictions(
    #     self,
    #     server_id: UUID,
    #     member_id: UUID
    # ) -> list[MemberRestrictionResponse]:
    #     """
    #     Get all restrictions for a member.
    #     Returns both active and expired restrictions.
    #     """
    #     # Verify member exists and belongs to server
    #     member = await self.member_repo.get_by_id(member_id)
    #     if not member or member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found in server {server_id}")
    #
    #     # Get all restrictions for the member
    #     restrictions = await self.member_restriction_repo.list_for_member(member_id)
    #
    #     # Convert to response models
    #     return [await self._to_member_restriction_response(restriction) for restriction in restrictions]
    #
    # async def add_restriction(
    #     self,
    #     server_id: UUID,
    #     member_id: UUID,
    #     body: MemberRestrictionCreateRequest
    # ) -> MemberRestrictionResponse:
    #     """
    #     Add a restriction to a member.
    #     Validates that the restriction code exists.
    #     """
    #     # Verify member exists and belongs to server
    #     member = await self.member_repo.get_by_id(member_id)
    #     if not member or member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found in server {server_id}")
    #
    #     # Verify restriction code exists
    #     restriction_code = await self.restriction_repo.get_by_id(body.restriction_id)
    #     if not restriction_code:
    #         raise NotFoundException(f"Restriction with id {body.restriction_id} not found")
    #
    #     # Create the member restriction
    #     member_restriction = await self.member_restriction_repo.create(
    #         member_id=member_id,
    #         restriction_code_id=body.restriction_id,
    #         reason=body.reason,
    #         expiration_date=body.expiration_date
    #     )
    #
    #     if not member_restriction:
    #         raise MigrationException()
    #
    #     return await self._to_member_restriction_response(member_restriction)
    #
    # async def remove_restriction(
    #     self,
    #     server_id: UUID,
    #     member_id: UUID,
    #     member_restriction_id: UUID
    # ) -> StatusResponse:
    #     """
    #     Remove a restriction from a member.
    #     """
    #     # Verify member exists and belongs to server
    #     member = await self.member_repo.get_by_id(member_id)
    #     if not member or member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found in server {server_id}")
    #
    #     # Get the restriction
    #     restriction = await self.member_restriction_repo.get_by_id(member_restriction_id)
    #     if not restriction or restriction.member_id != member_id:
    #         raise NotFoundException(f"Restriction with id {member_restriction_id} not found for member {member_id}")
    #
    #     # Delete the restriction
    #     await self.member_restriction_repo.delete(member_restriction_id)
    #
    #     return StatusResponse(status="ok")
