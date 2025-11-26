from uuid import UUID
from typing import Sequence
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from src.domain.exceptions import NotFoundException, MigrationException, InternalLogicException
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

    async def list_members(self, server_id: UUID) -> list[Member]:
        members = await self.member_repo.list_active_for_server(server_id)
        return list(members)

    async def join_server(self, server_id: UUID, user_id: UUID, name: str) -> Member:
        server = await self.server_repo.get_by_id(server_id)
        if not server or not server.public:
            raise NotFoundException(f"Server {server_id} not found")

        existing_member = await self.member_repo.get_by_user_in_server(server_id, user_id)
        if existing_member:
            # TODO: Handle bans and restrictions here
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
        body: VirtualMemberCreateRequest
    ) -> Member:
        # TODO: Check permissions to create virtual members
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

    async def get_member(self, server_id: UUID, member_id: UUID) -> Member:
        member = await self.member_repo.get_by_id(member_id)
        if not member or member.server_id != server_id:
            raise NotFoundException(f"Member with id {member_id} not found")
        return member

    # async def update_member(
    #     self,
    #     server_id: UUID,
    #     member_id: UUID,
    #     body: MemberUpdateRequest
    # ) -> MemberResponse:
    #     member = await self.member_repo.get_by_id(member_id)
    #     if not member or member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found")
    #
    #     if body.name and body.name != member.name:
    #         member = await self.member_repo.set_name(member, body.name)
    #
    #     if body.server_role_id is not None:
    #         # Validate that the role belongs to this server
    #         if body.server_role_id:
    #             role = await self.server_role_repo.get_by_id(body.server_role_id)
    #             if not role or role.server_id != server_id:
    #                 raise NotFoundException(f"Server role with id {body.server_role_id} not found in server {server_id}")
    #
    #         member = await self.member_repo.set_role(member, body.server_role_id)
    #
    #     # Update user_id if provided (only for virtual members)
    #     if body.user_id is not None:
    #         if member.user_id is None:
    #             # Check if user is already a member of this server
    #             existing_member = await self.member_repo.get_by_user_in_server(server_id, body.user_id)
    #             if existing_member:
    #                 raise MigrationException()
    #
    #             success = await self.member_repo.set_user_if_none(member, body.user_id)
    #             if not success:
    #                 raise MigrationException()
    #             # Refresh member
    #             member = await self.member_repo.get_by_id(member_id)
    #
    #     return await self._to_member_response(member)
    #
    # async def kick_member(self, server_id: UUID, member_id: UUID) -> StatusResponse:
    #     """
    #     Kick a member from the server (soft delete by deactivating).
    #     """
    #     member = await self.member_repo.get_by_id(member_id)
    #     if not member or member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found in server {server_id}")
    #
    #     # Deactivate the member (soft delete)
    #     await self.member_repo.deactivate(member)
    #
    #     return StatusResponse(status="ok")
    #
    # async def migrate_member(
    #     self,
    #     server_id: UUID,
    #     member_id: UUID,
    #     body: MigrationRequest
    # ) -> MemberResponse:
    #     """
    #     Migrate a virtual member to an existing member.
    #     Transfers all customs and data from the source member to the target member.
    #     """
    #     # Get source member (the one being migrated from)
    #     source_member = await self.member_repo.get_by_id(member_id)
    #     if not source_member or source_member.server_id != server_id:
    #         raise NotFoundException(f"Member with id {member_id} not found in server {server_id}")
    #
    #     # Get target member (the one being migrated to)
    #     target_member = await self.member_repo.get_by_id(body.target_member_id)
    #     if not target_member or target_member.server_id != server_id:
    #         raise NotFoundException(f"Target member with id {body.target_member_id} not found in server {server_id}")
    #
    #     # Ensure source is virtual (no user_id)
    #     if source_member.user_id is not None:
    #         raise MigrationException()
    #
    #     # Ensure target has a user
    #     if target_member.user_id is None:
    #         raise MigrationException()
    #
    #     # Migration: Transfer customs from source to target
    #     # This is handled by updating the customs' member_id
    #     # Since we're using the repository pattern, we would need a custom migration
    #     # For now, we'll deactivate the source member
    #     # In a full implementation, you'd transfer customs, ratings, etc.
    #
    #     await self.member_repo.deactivate(source_member)
    #
    #     # Return the target member
    #     return await self._to_member_response(target_member)
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
