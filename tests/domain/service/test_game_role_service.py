import uuid

import pytest
import pytest_asyncio

from src.core.exceptions import ForbiddenException, NotFoundException
from src.core.services.game_role import GameRoleService
from src.infra.postgre.repo import (
    GameRepository,
    GameRoleRepository,
    GameRoleSetRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def game_role_service(async_session):
    return GameRoleService(
        ServerRepository(async_session),
        GameRepository(async_session),
        GameRoleSetRepository(async_session),
        GameRoleRepository(async_session),
    )


async def _create_game(factory, game_repo, name="Game", server_id=None, min_rating=0, max_rating=50):
    game = await factory.create_game(name=name, server_id=server_id, min_rating=min_rating, max_rating=max_rating)
    detail = await game_repo.get_detail(game.id)
    assert detail is not None
    return detail


@pytest.mark.asyncio(loop_scope="session")
class TestGameRoleService:

    async def test_update_role_set_forbidden_without_permission(self, game_role_service, factory):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.update_role_set(server.id, game.role_set.id, name="NewName", permission_mask=0)

    async def test_update_role_set_not_found(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await game_role_service.update_role_set(
                server.id,
                uuid.uuid4(),
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_set_wrong_server(self, game_role_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server1.id)
        with pytest.raises(NotFoundException):
            await game_role_service.update_role_set(
                server2.id,
                game.role_set.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_set_success(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, name="Old", server_id=server.id)
        updated = await game_role_service.update_role_set(
            server.id,
            game.role_set.id,
            name="New",
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.name == "New"

    async def test_update_role_set_local_success_and_global_forbidden(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, game_role_service.game_repo)

        updated = await game_role_service.update_role_set(
            server.id,
            local_game.role_set.id,
            name="LocalUpdated",
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.name == "LocalUpdated"

        with pytest.raises(ForbiddenException, match="Unable to edit a global game role set"):
            await game_role_service.update_role_set(
                server.id,
                global_game.role_set.id,
                name="Hacked",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_global_role_set_global_success_and_local_forbidden(self, game_role_service, factory):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, game_role_service.game_repo)

        updated = await game_role_service.update_global_role_set(global_game.role_set.id, name="GlobalUpdated")
        assert updated.name == "GlobalUpdated"

        with pytest.raises(ForbiddenException, match="Role set does not belong to a global game"):
            await game_role_service.update_global_role_set(local_game.role_set.id, name="Hacked")

    async def test_create_role_forbidden_without_permission(self, game_role_service, factory):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.create_role(
                server.id,
                game.role_set.id,
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=0,
            )

    async def test_create_role_role_set_not_found(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await game_role_service.create_role(
                server.id,
                uuid.uuid4(),
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_create_role_wrong_server(self, game_role_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, game_role_service.game_repo, server_id=server1.id)

        with pytest.raises(NotFoundException):
            await game_role_service.create_role(
                server2.id,  # Wrong server
                game1.role_set.id,
                name="R",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_create_role_success(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        role = await game_role_service.create_role(
            server.id,
            game.role_set.id,
            name="Support",
            min_in_team=1,
            max_in_team=3,
            hidden=False,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert role is not None
        assert role.name == "Support"
        listed = await game_role_service.role_repo.list_for_set(game.role_set.id)
        assert any(r.id == role.id for r in listed)

    async def test_create_role_local_success_and_global_forbidden(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, game_role_service.game_repo)

        role = await game_role_service.create_role(
            server.id,
            local_game.role_set.id,
            name="LocalRole",
            min_in_team=1,
            max_in_team=2,
            hidden=False,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert role.name == "LocalRole"

        with pytest.raises(ForbiddenException, match="Unable to edit a global game role set"):
            await game_role_service.create_role(
                server.id,
                global_game.role_set.id,
                name="Hacked",
                min_in_team=1,
                max_in_team=2,
                hidden=False,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_create_global_role_global_success_and_local_forbidden(self, game_role_service, factory):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, game_role_service.game_repo)

        role = await game_role_service.create_global_role(
            global_game.role_set.id,
            name="GlobalRole",
            min_in_team=1,
            max_in_team=2,
        )
        assert role.name == "GlobalRole"

        with pytest.raises(ForbiddenException, match="Role set does not belong to a global game"):
            await game_role_service.create_global_role(
                local_game.role_set.id,
                name="Hacked",
                min_in_team=1,
                max_in_team=2,
            )

    async def test_update_role_forbidden_without_permission(self, game_role_service, factory):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.update_role(server.id, r.id, name="NewName", permission_mask=0)

    async def test_update_role_not_found(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await game_role_service.update_role(
                server.id,
                uuid.uuid4(),
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_wrong_server(self, game_role_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, game_role_service.game_repo, server_id=server1.id)
        r1 = await factory.create_game_role(game1.role_set.id)

        with pytest.raises(NotFoundException):
            await game_role_service.update_role(
                server2.id,  # Wrong server
                r1.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_role_success(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)
        new_icon = uuid.uuid4()
        updated = await game_role_service.update_role(
            server.id,
            r.id,
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

    async def test_update_role_local_success_and_global_forbidden(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        local_role = await factory.create_game_role(local_game.role_set.id)
        global_game = await _create_game(factory, game_role_service.game_repo)
        global_role = await factory.create_game_role(global_game.role_set.id)

        updated = await game_role_service.update_role(
            server.id,
            local_role.id,
            name="LocalRole",
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.name == "LocalRole"

        with pytest.raises(ForbiddenException, match="Unable to edit a global game role set"):
            await game_role_service.update_role(
                server.id,
                global_role.id,
                name="Hacked",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_update_global_role_global_success_and_local_forbidden(self, game_role_service, factory):
        server = await factory.create_server()
        local_game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        local_role = await factory.create_game_role(local_game.role_set.id)
        global_game = await _create_game(factory, game_role_service.game_repo)
        global_role = await factory.create_game_role(global_game.role_set.id)

        updated = await game_role_service.update_global_role(global_role.id, name="GlobalRole")
        assert updated.name == "GlobalRole"

        with pytest.raises(ForbiddenException, match="Role set does not belong to a global game"):
            await game_role_service.update_global_role(local_role.id, name="Hacked")

    async def test_delete_role_not_found(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await game_role_service.delete_role(
                server.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )

    async def test_delete_role_forbidden_without_permission(self, game_role_service, factory):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)
        with pytest.raises(ForbiddenException):
            await game_role_service.delete_role(server.id, r.id, permission_mask=0)

    async def test_delete_role_success(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)
        await game_role_service.delete_role(
            server.id,
            r.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert await game_role_service.role_repo.get(r.id) is None

    async def test_delete_role_icon_success(self, game_role_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)

        # Set an icon first
        r.icon_id = uuid.uuid4()
        await game_role_service.role_repo._session.flush()

        updated = await game_role_service.delete_role_icon(
            server.id,
            r.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
        )
        assert updated.icon_id is None

    async def test_delete_role_icon_forbidden(self, game_role_service, factory):
        server = await factory.create_server()
        game = await _create_game(factory, game_role_service.game_repo, server_id=server.id)
        r = await factory.create_game_role(game.role_set.id)

        with pytest.raises(ForbiddenException):
            await game_role_service.delete_role_icon(
                server.id,
                r.id,
                permission_mask=0,
            )

    async def test_delete_role_icon_not_found(self, game_role_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(NotFoundException):
            await game_role_service.delete_role_icon(
                server.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_ROLE_SET),
            )
