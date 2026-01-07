from uuid import UUID

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.domain.models.core.request import ServerCreateRequest, ServerUpdateRequest
from src.infra.postgre.models import Permission, Server, GameRoleSet, RatingSet, Restriction, Game
from src.infra.postgre.repo import (
    MemberRepository,
    ServerRepository,
    GameRoleRepository,
    GameRoleSetRepository,
    RatingRepository,
    RatingSetRepository,
    PermissionRepository,
    RestrictionRepository,
    GameRepository
)
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException

from src.infra.postgre.static import PERMISSION


class CoreService:
    def __init__(
            self,
            server_repo: ServerRepository,
            game_repo: GameRepository,
            game_role_repo: GameRoleRepository,
            game_role_set_repo: GameRoleSetRepository,
            rating_repo: RatingRepository,
            rating_set_repo: RatingSetRepository,
            permission_repo: PermissionRepository,
            restriction_repo: RestrictionRepository,
            member_repo: MemberRepository
    ) -> None:
        self.server_repo = server_repo
        self.game_repo = game_repo
        self.game_role_repo = game_role_repo
        self.game_role_set_repo = game_role_set_repo
        self.rating_repo = rating_repo
        self.rating_set_repo = rating_set_repo
        self.permission_repo = permission_repo
        self.restriction_repo = restriction_repo
        self.member_repo = member_repo

    async def get_global_role_templates(self) -> list[GameRoleSet]:
        return list(await self.game_role_set_repo.get_global())

    async def get_global_rating_templates(self) -> list[RatingSet]:
        return list(await self.rating_set_repo.get_global())

    async def get_global_permissions(self) -> list[Permission]:
        return list(await self.permission_repo.list_all())

    async def get_global_restrictions(self) -> list[Restriction]:
        return list(await self.restriction_repo.list_all())

    async def get_global_games(self) -> list[Game]:
        return list(await self.game_repo.get_all())

    async def list_servers(self) -> list[Server]:
        servers = await self.server_repo.list_public()
        return list(servers)

    async def list_user_servers(self, user_id: UUID) -> list[Server]:
        servers = await self.server_repo.list_by_owner(user_id)
        return list(servers)

    async def _copy_role_set(self, global_role_set: GameRoleSet) -> GameRoleSet:
        new_role_set = await self.game_role_set_repo.copy_global(global_role_set)
        for role_field in global_role_set.game_roles:
            new_role_field = await self.game_role_repo.copy_role(role_field, new_role_set.id)
            new_role_set.game_roles.append(new_role_field)
        return new_role_set

    async def _copy_rating_set(self, global_rating_set: RatingSet) -> RatingSet:
        new_rating_set = await self.rating_set_repo.copy_global(global_rating_set)
        for rating_field in global_rating_set.ratings:
            new_rating_field = await self.rating_repo.copy_rating(rating_field, new_rating_set.id)
            new_rating_set.ratings.append(new_rating_field)
        return new_rating_set

    async def create_server(
            self, owner_id: UUID,
            username: str,
            name: str,
            description: str,
            public: bool,
            rating_set_id: UUID | None = None,
            role_set_id: UUID | None = None
    ) -> Server:
        if role_set_id is None:
            raise NotFoundException("Role set ID must be provided")
        if rating_set_id is None:
            raise NotFoundException("Rating set ID must be provided")

        global_role_set = await self.game_role_set_repo.get_by_id(role_set_id)
        global_rating_set = await self.rating_set_repo.get_by_id(rating_set_id)
        if not global_role_set or not global_role_set.is_global:
            raise NotFoundException("Role set not found")
        if not global_rating_set or not global_rating_set.is_global:
            raise NotFoundException("Rating set not found")

        rating_set = await self._copy_rating_set(global_rating_set)
        role_set = await self._copy_role_set(global_role_set)

        try:
            server = await self.server_repo.create(
                name=name,
                owner_id=owner_id,
                role_set_id=role_set.id,
                rating_set_id=rating_set.id,
                public=public,
                description=description,
            )
            # links = await self.game_repo.bulk_add_to_server(server.id, body.game_ids)
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUniqueException, IntegrityUnknownException) as exc:
            raise InternalLogicException(exc.message)

        try:
            member_field = await self.member_repo.create(
                server_id=server.id,
                user_id=owner_id,
                nickname=username,
                server_role_id=None
            )
        except IntegrityForeignException as exc:
            raise NotFoundException(exc.message)
        except (IntegrityUnknownException, IntegrityUniqueException) as exc:
            raise InternalLogicException(exc.message)

        # server.server_games = links
        # server.games = [link.game for link in links]
        return server

    async def get_server(self, server_id: UUID) -> Server:
        server = await self.server_repo.get_by_id(server_id)
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
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if name is not None and name != server.name:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_NAME):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_name(server, name)
        if description is not None and description != server.description:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_DESCRIPTION):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_description(server, description)
        if public is not None and public != server.public:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_PUBLIC):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_public(server, public)
        if icon_id is not None and icon_id != server.icon_id:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ICON):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_icon(server, icon_id)
        if banner_id is not None and banner_id != server.banner_id:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_BANNER):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_banner(server, banner_id)
        return server

    async def delete_server(self, server_id: UUID, permission_mask: int = 0) -> None:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.DELETE_SERVER):
            raise ForbiddenException("Unable to delete server")
        ok = await self.server_repo.delete(server_id)
        if not ok:
            raise InternalLogicException("Failed to delete server")

    async def delete_server_banner(self, server_id: UUID, permission_mask: int = 0) -> Server:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_BANNER):
            raise ForbiddenException("Unable to edit server")
        return await self.server_repo.set_banner(server, None)

    async def delete_server_icon(self, server_id: UUID, permission_mask: int = 0) -> Server:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_ICON):
            raise ForbiddenException("Unable to edit server")
        return await self.server_repo.set_icon(server, None)

