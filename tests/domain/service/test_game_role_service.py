import uuid
import pytest
import pytest_asyncio

from src.core.services.game_role import GameRoleService
from src.core.exceptions import NotFoundException, ForbiddenException
from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo import (
    GameRoleSetRepository,
    GameRoleRepository,
    ServerRepository,
)


@pytest_asyncio.fixture(loop_scope="session")
async def game_role_service(async_session):
    return GameRoleService(
        ServerRepository(async_session),
        GameRoleSetRepository(async_session),
        GameRoleRepository(async_session)
    )


@pytest.mark.asyncio(loop_scope="session")
class TestGameRoleService:

    async def test_get_role_set_for_server_not_found(self, game_role_service):
        with pytest.raises(NotFoundException):
            await game_role_service.get_role_set_for_server(uuid.uuid4())

    async def test_get_role_set_for_server_success(self, game_role_service, factory):
        rs = await factory.create_role_set()
        s = await factory.create_server(role_set=rs)

        res = await game_role_service.get_role_set_for_server(s.id)
        assert res is not None
        assert res.id == rs.id

    async def test_update_role_set_forbidden_without_permission(self, game_role_service, factory):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(ForbiddenException):
            await game_role_service.update_role_set(rs.id, server.id, name="NewName", permission_mask=0)

    async def test_update_role_set_mismatch_raises_not_found(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(NotFoundException):
            await game_role_service.update_role_set(
                uuid.uuid4(),
                server.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_set_success(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set(name="Old")
        server = await factory.create_server(role_set=rs)
        updated = await game_role_service.update_role_set(
            rs.id,
            server.id,
            name="New",
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.name == "New"

    async def test_create_role_forbidden_without_permission(self, game_role_service, factory):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(ForbiddenException):
            await game_role_service.create_role(
                rs.id,
                server.id,
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=0
            )

    async def test_create_role_role_set_not_found(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(NotFoundException):
            await game_role_service.create_role(
                uuid.uuid4(),
                server.id,
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_create_role_wrong_server(self, game_role_service, factory, helpers):
        rs1 = await factory.create_role_set()
        await factory.create_server(role_set=rs1)
        s2 = await factory.create_server()

        with pytest.raises(NotFoundException):
            await game_role_service.create_role(
                rs1.id,
                s2.id,  # Wrong server
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_create_role_success(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        role = await game_role_service.create_role(
            rs.id,
            server.id,
            name="Support",
            min_in_team=1,
            max_in_team=3,
            hidden=False,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert role is not None
        assert role.name == "Support"
        listed = await game_role_service.role_repo.list_for_set(rs.id)
        assert any(r.id == role.id for r in listed)

    async def test_update_role_forbidden_without_permission(self, game_role_service, factory):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.update_role(r.id, server.id, name="NewName", permission_mask=0)

    async def test_update_role_not_found(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(NotFoundException):
            await game_role_service.update_role(
                uuid.uuid4(),
                server.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_wrong_server(self, game_role_service, factory, helpers):
        rs1 = await factory.create_role_set()
        await factory.create_server(role_set=rs1)
        r1 = await factory.create_game_role(rs1.id)

        s2 = await factory.create_server()

        with pytest.raises(NotFoundException):
            await game_role_service.update_role(
                r1.id,
                s2.id,  # Wrong server
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_success(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)
        new_icon = uuid.uuid4()
        updated = await game_role_service.update_role(
            r.id,
            server.id,
            name="NewName",
            min_in_team=2,
            max_in_team=4,
            icon_id=new_icon,
            hidden=True,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.name == "NewName"
        assert updated.hidden is True
        assert updated.min_in_team == 2
        assert updated.max_in_team == 4
        assert updated.icon_id == new_icon

    async def test_delete_role_not_found(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        with pytest.raises(NotFoundException):
            await game_role_service.delete_role(
                uuid.uuid4(),
                server.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_delete_role_forbidden_without_permission(self, game_role_service, factory):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.delete_role(r.id, server.id, permission_mask=0)

    async def test_delete_role_success(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)
        await game_role_service.delete_role(
            r.id,
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert await game_role_service.role_repo.get(r.id) is None

    async def test_delete_role_icon_success(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)

        # Set an icon first
        r.icon_id = uuid.uuid4()
        await game_role_service.role_repo._session.flush()

        updated = await game_role_service.delete_role_icon(
            r.id,
            server.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.icon_id is None

    async def test_delete_role_icon_forbidden(self, game_role_service, factory):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)
        r = await factory.create_game_role(rs.id)

        with pytest.raises(ForbiddenException):
            await game_role_service.delete_role_icon(
                r.id,
                server.id,
                permission_mask=0,
            )

    async def test_delete_role_icon_not_found(self, game_role_service, factory, helpers):
        rs = await factory.create_role_set()
        server = await factory.create_server(role_set=rs)

        with pytest.raises(NotFoundException):
            await game_role_service.delete_role_icon(
                uuid.uuid4(),
                server.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )
