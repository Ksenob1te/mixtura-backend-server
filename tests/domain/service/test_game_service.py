import uuid
import pytest
import pytest_asyncio

from src.core.services.game import GameService
from src.core.exceptions import NotFoundException, ForbiddenException
from src.infra.postgre.static import PERMISSION
from src.infra.postgre.repo import GameRepository, ServerRepository


@pytest_asyncio.fixture(loop_scope="session")
async def game_service(async_session):
    return GameService(
        game_repo=GameRepository(async_session),
        server_repo=ServerRepository(async_session),
    )


@pytest.mark.asyncio(loop_scope="session")
class TestGameService:

    async def test_list_server_games_not_found(self, game_service):
        with pytest.raises(NotFoundException):
            await game_service.list_server_games(uuid.uuid4())

    async def test_list_server_games_returns_linked_games(self, game_service, factory):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")
        g2 = await factory.create_game(name="G2")

        await game_service.game_repo.bulk_add_to_server(server.id, [g1.id, g2.id])

        res = await game_service.list_server_games(server.id)
        ids = {g.id for g in res}
        assert ids == {g1.id, g2.id}

    async def test_add_games_to_server_forbidden_without_permission(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")

        with pytest.raises(ForbiddenException):
            await game_service.add_games_to_server(
                server.id,
                [g1.id],
                permission_mask=helpers.perm_mask(),
            )

    async def test_add_games_to_server_not_found_server(self, game_service, factory, helpers):
        g1 = await factory.create_game(name="G1")

        with pytest.raises(NotFoundException):
            await game_service.add_games_to_server(
                uuid.uuid4(),
                [g1.id],
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )

    async def test_add_games_to_server_success(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")
        g2 = await factory.create_game(name="G2")

        await game_service.add_games_to_server(
            server.id,
            [g1.id, g2.id],
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )

        await game_service.server_repo._session.refresh(server)
        ids = {g.id for g in server.games}
        assert {g1.id, g2.id} == ids

    async def test_add_games_to_server_raises_when_some_games_missing(self, game_service, factory, helpers):
        server = await factory.create_server()
        existing = await factory.create_game(name="G1")
        missing_id = uuid.uuid4()

        with pytest.raises(NotFoundException):
            await game_service.add_games_to_server(
                server.id,
                [existing.id, missing_id],
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )

    async def test_remove_game_from_server_forbidden_without_permission(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")
        await game_service.game_repo.bulk_add_to_server(server.id, [g1.id])

        with pytest.raises(ForbiddenException):
            await game_service.remove_game_from_server(
                server.id,
                g1.id,
                permission_mask=helpers.perm_mask(),
            )

    async def test_remove_game_from_server_not_found_server(self, game_service, factory, helpers):
        g1 = await factory.create_game(name="G1")
        with pytest.raises(NotFoundException):
            await game_service.remove_game_from_server(
                uuid.uuid4(),
                g1.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )

    async def test_remove_game_from_server_success(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")
        g2 = await factory.create_game(name="G2")

        await game_service.game_repo.bulk_add_to_server(server.id, [g1.id, g2.id])

        await game_service.remove_game_from_server(
            server.id,
            g1.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )

        await game_service.server_repo._session.refresh(server)
        remaining_ids = {g.id for g in server.games}
        assert g1.id not in remaining_ids
        assert g2.id in remaining_ids

    async def test_remove_game_from_server_non_linked_raises_not_found(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")

        with pytest.raises(NotFoundException):
            await game_service.remove_game_from_server(
                server.id,
                g1.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )

    async def test_set_server_games_forbidden(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game()

        with pytest.raises(ForbiddenException):
            await game_service.set_server_games(
                server.id,
                [g1.id],
                permission_mask=helpers.perm_mask()
            )

    async def test_set_server_games_success(self, game_service, factory, helpers):
        server = await factory.create_server()
        g1 = await factory.create_game(name="G1")
        g2 = await factory.create_game(name="G2")
        g3 = await factory.create_game(name="G3")

        # Pre-populate with G1 and G2
        await game_service.game_repo.bulk_add_to_server(server.id, [g1.id, g2.id])

        # Set to G2 and G3 (should remove G1, keep G2, add G3)
        await game_service.set_server_games(
            server.id,
            [g2.id, g3.id],
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME)
        )

        await game_service.server_repo._session.refresh(server)
        current_ids = {g.id for g in server.games}
        assert current_ids == {g2.id, g3.id}
