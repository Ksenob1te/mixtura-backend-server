from uuid import UUID

from src.core.exceptions import (
    ForbiddenException,
    IntegrityForeignException,
    IntegrityUniqueException,
    IntegrityUnknownException,
    InternalLogicException,
    NotFoundException,
)
from src.core.interfaces.repo.member import MemberRepositoryProtocol
from src.core.interfaces.repo.permission import PermissionRepositoryProtocol
from src.core.interfaces.repo.restriction import RestrictionRepositoryProtocol
from src.core.interfaces.repo.server import ServerRepositoryProtocol
from src.core.models.member import MemberCreate
from src.core.models.permission import Permission
from src.core.models.restriction import Restriction
from src.core.models.server import Server, ServerCreate, ServerUpdate
from src.infra.postgre.static import PERMISSION


class CoreService:
    def __init__(
            self,
            server_repo: ServerRepositoryProtocol,
            permission_repo: PermissionRepositoryProtocol,
            restriction_repo: RestrictionRepositoryProtocol,
            member_repo: MemberRepositoryProtocol
    ) -> None:
        self.server_repo = server_repo
        self.permission_repo = permission_repo
        self.restriction_repo = restriction_repo
        self.member_repo = member_repo

    async def get_global_permissions(self) -> list[Permission]:
        return list(await self.permission_repo.list_all())

    async def get_global_restrictions(self) -> list[Restriction]:
        return list(await self.restriction_repo.list_all())

    async def list_servers(
            self, page: int | None = None,
            name_filter: str | None = None,
            page_size: int = 50
    ) -> list[Server]:
        servers = await self.server_repo.list_public(page, name_filter, page_size)
        return list(servers)

    async def list_user_servers(
            self, user_id: UUID,
            page: int | None = None,
            name_filter: str | None = None,
            page_size: int = 50
    ) -> list[Server]:
        servers = await self.server_repo.list_by_user(user_id, page, name_filter, page_size)
        return list(servers)

    async def create_server(
            self, name: str, owner_id: UUID, username: str,
            description: str,
            public: bool
    ) -> Server:
        try:
            server = await self.server_repo.create(
                ServerCreate(name=name, owner_id=owner_id, public=public, description=description)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUniqueException, IntegrityUnknownException) as exc:
            raise InternalLogicException(exc.message)

        try:
            await self.member_repo.create(
                MemberCreate(server_id=server.id, user_id=owner_id, nickname=username)
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUnknownException, IntegrityUniqueException) as exc:
            raise InternalLogicException(exc.message)

        return server

    async def get_server(self, server_id: UUID) -> Server:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server

    async def update_server(self, server_id: UUID,
                            name: str | None = None,
                            description: str | None = None,
                            public: bool | None = None,
                            banner_id: UUID | None = None,
                            icon_id: UUID | None = None,
                            permission_mask: int = 0) -> Server:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")

        update_data: dict = {}
        if name is not None and name != server.name:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_NAME):
                raise ForbiddenException("Unable to edit server")
            update_data["name"] = name
        if description is not None and description != server.description:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_DESCRIPTION):
                raise ForbiddenException("Unable to edit server")
            update_data["description"] = description
        if public is not None and public != server.public:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_PUBLIC):
                raise ForbiddenException("Unable to edit server")
            update_data["public"] = public
        if icon_id is not None and icon_id != server.icon_id:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ICON):
                raise ForbiddenException("Unable to edit server")
            update_data["icon_id"] = icon_id
        if banner_id is not None and banner_id != server.banner_id:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_BANNER):
                raise ForbiddenException("Unable to edit server")
            update_data["banner_id"] = banner_id

        if update_data:
            server = await self.server_repo.update(ServerUpdate(id=server_id, **update_data))
        return server

    async def delete_server(self, server_id: UUID, permission_mask: int = 0) -> None:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.DELETE_SERVER):
            raise ForbiddenException("Unable to delete server")
        ok = await self.server_repo.delete(server_id)
        if not ok:
            raise InternalLogicException("Failed to delete server")

    async def delete_server_banner(self, server_id: UUID, permission_mask: int = 0) -> Server:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_BANNER):
            raise ForbiddenException("Unable to edit server")
        return await self.server_repo.update(ServerUpdate(id=server_id, banner_id=None))

    async def delete_server_icon(self, server_id: UUID, permission_mask: int = 0) -> Server:
        server = await self.server_repo.get(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ICON):
            raise ForbiddenException("Unable to edit server")
        return await self.server_repo.update(ServerUpdate(id=server_id, icon_id=None))
