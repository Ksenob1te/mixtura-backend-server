from uuid import UUID
from fastapi import UploadFile
from sqlalchemy import exc

from src.domain.exceptions import NotFoundException, ForbiddenException, InternalLogicException
from src.domain.models.game_roles.request import (
    GameRoleItemCreateRequest,
    GameRoleItemUpdateRequest,
    GameRoleSetUpdateRequest,
)
from src.infra.postgre.models import GameRoleSet, GameRole
from src.infra.postgre.repo import (
    GameRoleSetRepository,
    GameRoleRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION
from src.infra.postgre import IntegrityForeignException, IntegrityUnknownException


class GameRoleService:
    def __init__(
        self,
        server_repo: ServerRepository,
        role_set_repo: GameRoleSetRepository,
        role_repo: GameRoleRepository,
    ) -> None:
        self.server_repo = server_repo
        self.role_set_repo = role_set_repo
        self.role_repo = role_repo

    async def get_role_set_for_server(self, server_id: UUID) -> GameRoleSet:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server.role_set

    async def update_role_set(
        self, role_set_id: UUID, body: GameRoleSetUpdateRequest, permission_mask: int = 0
    ) -> GameRoleSet:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_set_field = await self.role_set_repo.get_by_id(role_set_id)
        if role_set_field is None:
            raise NotFoundException("Role set not found")
        if body.name is not None and body.name != role_set_field.name:
            role_set_field = await self.role_set_repo.set_name(role_set_field, body.name)
        return role_set_field

    async def create_role(
        self,
        role_set_id: UUID,
        body: GameRoleItemCreateRequest,
        permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role_set_field = await self.role_set_repo.get_by_id(role_set_id)
        if not role_set_field:
            raise NotFoundException("Role set not found for server")

        icon_url = None
        icon_id = None
        # if icon is not None:
        # TODO: upload icon to minio

        try:
            role = await self.role_repo.create(
                name=body.name,
                role_set_id=role_set_id,
                min_in_team=body.min_in_team,
                max_in_team=body.max_in_team,
                icon_url=icon_url,
                icon_id=icon_id,
                hidden=body.hidden,
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except IntegrityUnknownException as exc:
            raise InternalLogicException(exc.message)
        return role

    async def update_role(
        self,
        role_id: UUID,
        body: GameRoleItemUpdateRequest,
        permission_mask: int = 0,
    ) -> GameRole:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to edit role set")
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundException("Role not found")

        if body.name is not None and body.name != role.name:
            role = await self.role_repo.set_name(role, body.name)
        if body.hidden is not None and body.hidden != role.hidden:
            role = await self.role_repo.set_hidden(role, body.hidden)
        if body.min_in_team is not None:
            role = await self.role_repo.set_min(role, body.min_in_team)
        if body.max_in_team is not None:
            role = await self.role_repo.set_max(role, body.max_in_team)
        return role

    async def delete_role(self, role_id: UUID, permission_mask: int = 0) -> None:
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
            raise ForbiddenException("Unable to delete role")
        deleted = await self.role_repo.delete(role_id)
        if not deleted:
            raise NotFoundException("Role not found")

    # async def update_role_icon(
    #     self, server_id: UUID, role_id: UUID, role_set_id: UUID, icon: UploadFile | None, permission_mask: int = 0
    # ) -> GameRole:
    #     server = await self.server_repo.get_by_id(server_id)
    #     if not server:
    #         raise NotFoundException("Server not found")
    #     role = await self.role_repo.get_by_id(role_id)
    #     if not role or role.role_set_id != role_set_id:
    #         raise NotFoundException("Role not found")
    #     if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_ROLE_SET):
    #         raise ForbiddenException("Unable to edit role icon")
    #
    #     if icon is None:
    #         # remove icon
    #         role = await self.role_repo.set_icon(role, None, None)
    #         return role
    #
    #     content = await icon.read()
    #     filename = icon.filename
    #     prefix = f"role_icons/{role_set_id}"
    #     await minio_manager.upload_file_object(prefix, filename, content)
    #     icon_url = f"{minio_manager.endpoint}/{minio_manager.bucket_name}/{prefix}/{filename}"
    #     role = await self.role_repo.set_icon(role, icon_url, None)
    #     return role
