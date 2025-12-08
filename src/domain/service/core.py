from uuid import UUID
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions import NotFoundException, InternalLogicException, ForbiddenException
from src.domain.models.core.request import ServerCreateRequest, ServerUpdateRequest
from src.infra.postgre.models import Server, GameRoleSet, RatingSet, Restriction, Game
from src.infra.postgre.repo import (MemberRepository, ServerRepository, GameRoleSetRepository, RatingSetRepository,
                                    RestrictionRepository, GameRepository)

from src.infra.postgre.static import PERMISSION


class CoreService:
    def __init__(
            self,
            server_repo: ServerRepository,
            game_repo: GameRepository,
            game_role_set_repo: GameRoleSetRepository,
            rating_set_repo: RatingSetRepository,
            restriction_repo: RestrictionRepository,
            member_repo: MemberRepository
    ) -> None:
        self.server_repo = server_repo
        self.game_repo = game_repo
        self.game_role_set_repo = game_role_set_repo
        self.rating_set_repo = rating_set_repo
        self.restriction_repo = restriction_repo
        self.member_repo = member_repo

    async def get_global_role_templates(self) -> list[GameRoleSet]:
        return list(await self.game_role_set_repo.get_global())

    async def get_global_rating_templates(self) -> list[RatingSet]:
        return list(await self.rating_set_repo.get_global())

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

    async def create_server(self, owner_id: UUID, body: ServerCreateRequest) -> Server:
        role_set_field = None
        rating_set_field = None

        if body.role_set_id is not None:
            role_set_field = await self.game_role_set_repo.get_by_id(body.role_set_id)
        if role_set_field is None:
            raise NotFoundException("Role set not found")

        if body.rating_set_id is not None:
            rating_set_field = await self.rating_set_repo.get_by_id(body.rating_set_id)
        if rating_set_field is None:
            raise NotFoundException("Rating set not found")

        try:
            server = await self.server_repo.create(
                name=body.name,
                owner_id=owner_id,
                role_set_id=role_set_field.id,
                rating_set_id=rating_set_field.id,
                public=body.public,
                description=body.description,
            )
        except IntegrityError:
            raise InternalLogicException("Failed to create server due to integrity error")
        if server is None:
            raise InternalLogicException("Failed to create server")
        try:
            links = await self.game_repo.bulk_add_to_server(server.id, body.game_ids)
        except IntegrityError as exc:
            # SQLSTATE_FK_VIOLATION - some games do not exist
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise NotFoundException("Some games are not found")
            raise InternalLogicException("Failed to add games to server")

        server.server_games = links
        server.games = [link.game for link in links]
        return server

    async def get_server(self, server_id: UUID) -> Server:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        return server

    async def update_server(self, server_id: UUID, body: ServerUpdateRequest,
                            permission_mask: int = 0) -> Server:
        server = await self.server_repo.get_by_id(server_id)
        if not server:
            raise NotFoundException("Server not found")
        if body.name is not None and body.name != server.name:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_NAME):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_name(server, body.name)
        if body.description is not None and body.description != server.description:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_DESCRIPTION):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_description(server, body.description)
        if body.public is not None and body.public != server.public:
            if not PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_SERVER_PUBLIC):
                raise ForbiddenException("Unable to edit server")
            server = await self.server_repo.set_public(server, body.public)
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

    # TODO: add S3 services for updating logo and banner images
