import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_session

from src.domain.service.core import CoreService
from src.domain.exceptions import NotFoundException, ForbiddenException
from src.infra.postgre.static import PERMISSION
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
from src.infra.postgre.models import Server


@pytest_asyncio.fixture(loop_scope="session")
async def core_service(async_session):
    return CoreService(
        server_repo=ServerRepository(async_session),
        game_repo=GameRepository(async_session),
        game_role_repo=GameRoleRepository(async_session),
        game_role_set_repo=GameRoleSetRepository(async_session),
        rating_repo=RatingRepository(async_session),
        rating_set_repo=RatingSetRepository(async_session),
        permission_repo=PermissionRepository(async_session),
        restriction_repo=RestrictionRepository(async_session),
        member_repo=MemberRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestCoreService:

    async def test_get_global_role_templates(self, core_service, factory):
        await factory.create_role_set(is_global=True)
        await factory.create_role_set(is_global=False)

        res = await core_service.get_global_role_templates()
        assert len(res) >= 1
        assert all(rs.is_global for rs in res)

    async def test_get_global_rating_templates(self, core_service, factory):
        await factory.create_rating_set(is_global=True)
        await factory.create_rating_set(is_global=False)

        res = await core_service.get_global_rating_templates()
        assert len(res) >= 1
        assert all(rts.is_global for rts in res)

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

    async def test_get_global_games(self, core_service, factory):
        g1 = await factory.create_game(name="G1")
        g2 = await factory.create_game(name="G2")

        res = await core_service.get_global_games()
        ids = {g.id for g in res}
        assert {g1.id, g2.id}.issubset(ids)

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

    async def test_list_user_servers_filters_by_owner(self, core_service, factory):
        owner_id = uuid.uuid4()
        other_owner_id = uuid.uuid4()

        await factory.create_server(owner_id=owner_id)
        await factory.create_server(owner_id=other_owner_id)

        res = await core_service.list_user_servers(owner_id)
        assert len(res) >= 1
        assert all(s.owner_id == owner_id for s in res)

    async def test_list_user_servers_filtering(self, core_service, factory):
        owner_id = uuid.uuid4()
        await factory.create_server(owner_id=owner_id, name="MyGameServer")
        await factory.create_server(owner_id=owner_id, name="MyChatServer")
        await factory.create_server(owner_id=owner_id, name="OtherServer")

        # Test name filter
        res = await core_service.list_user_servers(owner_id, name_filter="My")
        assert len(res) == 2
        assert all("My" in s.name for s in res)

        # Test pagination
        res_page = await core_service.list_user_servers(owner_id, name_filter="My", page=0, page_size=1)
        assert len(res_page) == 1

    async def test_create_server_raises_when_role_set_not_found(self, core_service, factory):
        rating = await factory.create_rating_set()

        with pytest.raises(NotFoundException):
            await core_service.create_server(
                owner_id=uuid.uuid4(),
                username="Owner",
                name="NewServer",
                description="Desc",
                public=True,
                role_set_id=uuid.uuid4(),
                rating_set_id=rating.id
            )

    async def test_create_server_raises_when_rating_set_not_found(self, core_service, factory):
        role_set = await factory.create_role_set()

        with pytest.raises(NotFoundException):
            await core_service.create_server(
                owner_id=uuid.uuid4(),
                username="Owner",
                name="NewServer",
                description="Desc",
                public=True,
                role_set_id=role_set.id,
                rating_set_id=uuid.uuid4()
            )

    async def test_create_server_raises_when_template_is_not_global(self, core_service, factory):
        owner_id = uuid.uuid4()
        global_role_set = await factory.create_role_set(is_global=True)
        local_role_set = await factory.create_role_set(is_global=False)
        global_rating_set = await factory.create_rating_set(is_global=True)
        local_rating_set = await factory.create_rating_set(is_global=False)

        with pytest.raises(NotFoundException):
            await core_service.create_server(
                owner_id=owner_id,
                username="Owner",
                name="BadRole",
                description="Desc",
                public=True,
                role_set_id=local_role_set.id,
                rating_set_id=global_rating_set.id
            )

        with pytest.raises(NotFoundException):
            await core_service.create_server(
                owner_id=owner_id,
                username="Owner",
                name="BadRating",
                description="Desc",
                public=True,
                role_set_id=global_role_set.id,
                rating_set_id=local_rating_set.id
            )

    async def test_create_server_success_persists(self, core_service, factory):
        owner_id = uuid.uuid4()
        global_role_set = await factory.create_role_set(is_global=True)
        global_rating_set = await factory.create_rating_set(is_global=True)

        server = await core_service.create_server(
            owner_id=owner_id,
            username="OwnerNickname",
            name="ServerName",
            description="Desc",
            public=True,
            role_set_id=global_role_set.id,
            rating_set_id=global_rating_set.id
        )
        assert server is not None
        assert server.name == "ServerName"
        assert server.owner_id == owner_id

        member = await core_service.member_repo.get_by_user_in_server(server.id, owner_id)
        assert member is not None
        assert member.nickname == "OwnerNickname"

        assert server.role_set != global_role_set
        assert server.rating_set != global_rating_set

        new_role_set = await core_service.game_role_set_repo.get_by_id(server.role_set.id)
        new_rating_set = await core_service.rating_set_repo.get_by_id(server.rating_set.id)

        assert new_role_set is not None
        assert new_role_set.is_global is False
        assert new_rating_set is not None
        assert new_rating_set.is_global is False

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
        assert await core_service.server_repo.get_by_id(server.id) is None

    async def test_delete_server_banner(self, core_service, factory, helpers):
        server = await factory.create_server()
        server.banner_id = uuid.uuid4()
        await core_service.server_repo.session.flush()

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
        await core_service.server_repo.session.flush()

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

    async def test_delete_server_cascades_to_sets(self, core_service, factory, helpers):
        owner_id = uuid.uuid4()
        global_role_set = await factory.create_role_set(is_global=True)
        global_rating_set = await factory.create_rating_set(is_global=True)

        server = await core_service.create_server(
            owner_id=owner_id,
            username="Owner",
            name="ToDelete",
            description="Desc",
            public=True,
            role_set_id=global_role_set.id,
            rating_set_id=global_rating_set.id
        )

        role_set_id = server.role_set.id
        rating_set_id = server.rating_set.id

        # Verify existence before delete
        assert await core_service.game_role_set_repo.get_by_id(role_set_id) is not None
        assert await core_service.rating_set_repo.get_by_id(rating_set_id) is not None

        await core_service.delete_server(
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.DELETE_SERVER)
        )
        # Verify server is gone
        assert await core_service.server_repo.get_by_id(server.id) is None

        # Verify sets are gone
        assert await core_service.game_role_set_repo.get_by_id(role_set_id) is None
        assert await core_service.rating_set_repo.get_by_id(rating_set_id) is None
