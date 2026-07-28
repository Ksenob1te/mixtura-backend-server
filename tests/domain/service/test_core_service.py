import uuid

import pytest
import pytest_asyncio

from src.core.exceptions import ForbiddenException, NotFoundException
from src.core.models.member import MemberUpdate
from src.core.services.core import CoreService
from src.infra.postgre.repo import (
    GameRepository,
    GameRoleSetRepository,
    MemberRepository,
    PermissionRepository,
    RatingSetRepository,
    RestrictionRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def core_service(async_session):
    return CoreService(
        server_repo=ServerRepository(async_session),
        permission_repo=PermissionRepository(async_session),
        restriction_repo=RestrictionRepository(async_session),
        member_repo=MemberRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestCoreService:

    async def test_get_global_permissions(self, core_service, factory):
        await factory.create_permission(code="P1")
        await factory.create_permission(code="P2")

        res = await core_service.get_global_permissions()
        codes = {r.code for r in res}
        assert "P1" in codes and "P2" in codes

    async def test_get_global_restrictions(self, core_service, factory):
        await factory.create_restriction(code="R1")
        await factory.create_restriction(code="R2")

        res = await core_service.get_global_restrictions()
        codes = {r.code for r in res}
        assert "R1" in codes and "R2" in codes

    async def test_list_servers_returns_only_public(self, core_service, factory):
        await factory.create_server(public=True)
        await factory.create_server(public=False)

        res = await core_service.list_servers()
        assert all(s.public for s in res)

    async def test_list_servers_filtering(self, core_service, factory):
        await factory.create_server(name="AlphaServer", public=True)
        await factory.create_server(name="BetaServer", public=True)
        await factory.create_server(name="AlphaTwo", public=True)

        # Test name filter
        res = await core_service.list_servers(name_filter="Alpha")
        assert len(res) == 2
        assert all("Alpha" in s.name for s in res)

        # Test pagination
        res_page_1 = await core_service.list_servers(name_filter="Alpha", page=1, page_size=1)
        assert len(res_page_1) == 1
        res_page_2 = await core_service.list_servers(name_filter="Alpha", page=2, page_size=1)
        assert len(res_page_2) == 1
        assert res_page_1[0].id != res_page_2[0].id

    async def test_list_user_servers_returns_only_active_members(self, core_service, factory):
        user_id = uuid.uuid4()

        active_server = await factory.create_server(name="ActiveServer")
        inactive_server = await factory.create_server(name="InactiveServer")

        await factory.create_member(active_server.id, user_id=user_id)
        inactive_member = await factory.create_member(inactive_server.id, user_id=user_id)

        await core_service.member_repo.update(MemberUpdate(id=inactive_member.id, active=False))

        res = await core_service.list_user_servers(user_id)
        assert len(res) == 1
        assert res[0].id == active_server.id

    async def test_list_user_servers_name_filter(self, core_service, factory):
        user_id = uuid.uuid4()

        s1 = await factory.create_server(name="AlphaServer")
        s2 = await factory.create_server(name="BetaServer")
        s3 = await factory.create_server(name="AlphaTwo")

        await factory.create_member(s1.id, user_id=user_id)
        await factory.create_member(s2.id, user_id=user_id)
        await factory.create_member(s3.id, user_id=user_id)

        res = await core_service.list_user_servers(user_id, name_filter="Alpha")
        assert len(res) == 2
        assert all("Alpha" in s.name for s in res)

    async def test_list_user_servers_pagination(self, core_service, factory):
        user_id = uuid.uuid4()

        servers = [await factory.create_server(name=f"Server{i}") for i in range(5)]
        for s in servers:
            await factory.create_member(s.id, user_id=user_id)

        res_page1 = await core_service.list_user_servers(user_id, page=1, page_size=2)
        res_page2 = await core_service.list_user_servers(user_id, page=2, page_size=2)
        res_page3 = await core_service.list_user_servers(user_id, page=3, page_size=2)

        assert len(res_page1) == 2
        assert len(res_page2) == 2
        assert len(res_page3) == 1
        ids = {s.id for s in res_page1 + res_page2 + res_page3}
        assert len(ids) == 5

    async def test_create_server_success_persists(self, core_service):
        owner_id = uuid.uuid4()

        server = await core_service.create_server(
            owner_id=owner_id,
            username="OwnerNickname",
            name="ServerName",
            description="Desc",
            public=True,
        )
        assert server is not None
        assert server.name == "ServerName"
        assert server.description == "Desc"
        assert server.public is True
        assert server.owner_id == owner_id

        member = await core_service.member_repo.get_by_user_in_server(server.id, owner_id)
        assert member is not None
        assert member.nickname == "OwnerNickname"

    async def test_get_server_permission(self, core_service, factory):
        public_server = await factory.create_server(public=True)
        fetched_public = await core_service.get_server(public_server.id)
        assert fetched_public.id == public_server.id

        private_server = await factory.create_server(public=False)
        fetched_private = await core_service.get_server(private_server.id)
        assert fetched_private.id == private_server.id

    async def test_get_server_not_found(self, core_service):
        with pytest.raises(NotFoundException):
            await core_service.get_server(uuid.uuid4())

    async def test_update_server_not_found(self, core_service):
        with pytest.raises(NotFoundException):
            await core_service.update_server(uuid.uuid4(), name="NewName", permission_mask=0)

    async def test_update_server_updates_fields_with_permissions(self, core_service, factory, helpers):
        server = await factory.create_server(public=False)

        updated = await core_service.update_server(
            server.id,
            name="NewName",
            description="NewDesc",
            public=True,
            permission_mask=helpers.perm_mask(
                PERMISSION.EDIT_SERVER_NAME,
                PERMISSION.EDIT_SERVER_DESCRIPTION,
                PERMISSION.EDIT_SERVER_PUBLIC,
            ),
        )

        assert updated.name == "NewName"
        assert updated.description == "NewDesc"
        assert updated.public is True

    async def test_update_server_without_permissions(self, core_service, factory, helpers):
        server = await factory.create_server(public=False)

        with pytest.raises(ForbiddenException):
            await core_service.update_server(
                server.id,
                name="AnotherName",
                description="AnotherDesc",
                public=True,
                permission_mask=helpers.perm_mask(),
            )

    async def test_delete_server_permission_and_flow(self, core_service, factory, helpers):
        server = await factory.create_server(public=True)

        with pytest.raises(ForbiddenException):
            await core_service.delete_server(server.id, permission_mask=helpers.perm_mask())

        with pytest.raises(NotFoundException):
            await core_service.delete_server(uuid.uuid4(), permission_mask=helpers.perm_mask(PERMISSION.DELETE_SERVER))

        await core_service.delete_server(server.id, permission_mask=helpers.perm_mask(PERMISSION.DELETE_SERVER))
        assert await core_service.server_repo.get(server.id) is None

    async def test_delete_server_banner(self, core_service, factory, helpers):
        server = await factory.create_server()
        server.banner_id = uuid.uuid4()
        await core_service.server_repo._session.flush()

        with pytest.raises(ForbiddenException):
            await core_service.delete_server_banner(server.id, permission_mask=0)

        updated = await core_service.delete_server_banner(
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_BANNER)
        )
        assert updated.banner_id is None

    async def test_delete_server_icon(self, core_service, factory, helpers):
        server = await factory.create_server()
        server.icon_id = uuid.uuid4()
        await core_service.server_repo._session.flush()

        with pytest.raises(ForbiddenException):
            await core_service.delete_server_icon(server.id, permission_mask=0)

        updated = await core_service.delete_server_icon(
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ICON)
        )
        assert updated.icon_id is None

    async def test_delete_server_assets_not_found(self, core_service, helpers):
        with pytest.raises(NotFoundException):
            await core_service.delete_server_banner(
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_BANNER)
            )

        with pytest.raises(NotFoundException):
            await core_service.delete_server_icon(
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_ICON)
            )

    async def test_delete_server_cascades_to_local_game_but_not_global(
        self, core_service, factory, helpers, async_session
    ):
        server = await factory.create_server(public=True)
        local_game = await factory.create_game(name="LocalGame", server_id=server.id)
        global_game = await factory.create_game(name="GlobalGame")
        await factory.attach_game(server.id, local_game.id)

        game_repo = GameRepository(async_session)
        role_set_repo = GameRoleSetRepository(async_session)
        rating_set_repo = RatingSetRepository(async_session)

        local_detail = await game_repo.get_detail(local_game.id)
        assert local_detail is not None
        local_role_set_id = local_detail.role_set.id
        local_rating_set_id = local_detail.rating_set.id

        # Verify existence before delete
        assert await game_repo.get(local_game.id) is not None
        assert await role_set_repo.get(local_role_set_id) is not None
        assert await rating_set_repo.get(local_rating_set_id) is not None

        await core_service.delete_server(
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.DELETE_SERVER)
        )
        # Verify server is gone
        assert await core_service.server_repo.get(server.id) is None

        # Verify the local game and its sets are gone
        assert await game_repo.get(local_game.id) is None
        assert await role_set_repo.get(local_role_set_id) is None
        assert await rating_set_repo.get(local_rating_set_id) is None

        # Verify the global game survives
        assert await game_repo.get(global_game.id) is not None
