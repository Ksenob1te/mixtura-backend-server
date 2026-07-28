import uuid

import pytest
import pytest_asyncio

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from src.core.services.rating import RatingService
from src.infra.postgre.repo import (
    GameRepository,
    RatingRepository,
    RatingSetRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def rating_service(async_session):
    return RatingService(
        RatingRepository(async_session),
        RatingSetRepository(async_session),
        ServerRepository(async_session),
        GameRepository(async_session),
    )


async def _create_game(factory, game_repo, name="Game", server_id=None, min_rating=0, max_rating=50):
    game = await factory.create_game(name=name, server_id=server_id, min_rating=min_rating, max_rating=max_rating)
    detail = await game_repo.get_detail(game.id)
    assert detail is not None
    return detail


@pytest.mark.asyncio(loop_scope="session")
class TestRatingService:

    async def test_update_rating_set_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        with pytest.raises(ForbiddenException):
            await rating_service.update_rating_set(
                server.id,
                game.rating_set.id,
                name="NewName",
                min_rating=10,
                max_rating=100,
                permission_mask=helpers.perm_mask(),
            )

    async def test_update_rating_set_not_found(self, rating_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await rating_service.update_rating_set(
                server.id,
                uuid.uuid4(),
                name="NewName",
                min_rating=10,
                max_rating=100,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_set_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, rating_service.game_repo, server_id=server1.id)
        with pytest.raises(NotFoundException):
            await rating_service.update_rating_set(
                server2.id,
                game1.rating_set.id,
                name="NewName",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_set_success(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        updated = await rating_service.update_rating_set(
            server.id,
            game.rating_set.id,
            name="NewName",
            min_rating=10,
            max_rating=100,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert updated.name == "NewName"
        assert updated.min_rating == 10
        assert updated.max_rating == 100

    async def test_update_rating_set_bounds_invalid(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        with pytest.raises(BadRequestException, match="Rating bounds are invalid"):
            await rating_service.update_rating_set(
                server.id,
                game.rating_set.id,
                min_rating=100,
                max_rating=10,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_set_local_success_and_global_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, rating_service.game_repo)

        updated = await rating_service.update_rating_set(
            server.id,
            local_game.rating_set.id,
            name="LocalUpdated",
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert updated.name == "LocalUpdated"

        with pytest.raises(ForbiddenException, match="Unable to edit a global game rating set"):
            await rating_service.update_rating_set(
                server.id,
                global_game.rating_set.id,
                name="Hacked",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_global_rating_set_global_success_and_local_forbidden(self, rating_service, factory):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, rating_service.game_repo)

        updated = await rating_service.update_global_rating_set(global_game.rating_set.id, name="GlobalUpdated")
        assert updated.name == "GlobalUpdated"

        with pytest.raises(ForbiddenException, match="Rating set does not belong to a global game"):
            await rating_service.update_global_rating_set(local_game.rating_set.id, name="Hacked")

    async def test_create_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        with pytest.raises(ForbiddenException):
            await rating_service.create_rating(
                server.id,
                game.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(),
            )

    async def test_create_rating_not_found_rating_set(self, rating_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(NotFoundException):
            await rating_service.create_rating(
                server.id,
                uuid.uuid4(),
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_create_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, rating_service.game_repo, server_id=server1.id)

        with pytest.raises(NotFoundException):
            await rating_service.create_rating(
                server2.id,
                game1.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_create_rating_local_success_and_global_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, rating_service.game_repo)

        created = await rating_service.create_rating(
            server.id,
            local_game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert created.threshold == 10

        with pytest.raises(ForbiddenException, match="Unable to edit a global game rating set"):
            await rating_service.create_rating(
                server.id,
                global_game.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_create_global_rating_global_success_and_local_forbidden(self, rating_service, factory):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        global_game = await _create_game(factory, rating_service.game_repo)

        created = await rating_service.create_global_rating(
            global_game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
        )
        assert created.threshold == 10

        with pytest.raises(ForbiddenException, match="Rating set does not belong to a global game"):
            await rating_service.create_global_rating(
                local_game.rating_set.id,
                threshold=10,
                icon_id=uuid.uuid4(),
            )

    async def test_create_and_update_and_delete_rating(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        created = await rating_service.create_rating(
            server.id,
            game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert created.threshold == 10
        assert created.rating_set_id == game.rating_set.id

        updated = await rating_service.update_rating(
            server.id,
            created.id,
            threshold=20,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        assert updated.threshold == 20

        await rating_service.delete_rating(
            server.id,
            created.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.update_rating(
                server.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        created = await rating_service.create_rating(
            server.id,
            game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(ForbiddenException):
            await rating_service.update_rating(
                server.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(),
            )

    async def test_update_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, rating_service.game_repo, server_id=server1.id)

        created = await rating_service.create_rating(
            server1.id,
            game1.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.update_rating(
                server2.id,
                created.id,
                threshold=20,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_rating_local_success_and_global_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        local_rating = await rating_service.create_rating(
            server.id,
            local_game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        global_game = await _create_game(factory, rating_service.game_repo)
        global_rating = await rating_service.create_global_rating(global_game.rating_set.id, threshold=5)

        updated = await rating_service.update_rating(
            server.id,
            local_rating.id,
            threshold=30,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert updated.threshold == 30

        with pytest.raises(ForbiddenException, match="Unable to edit a global game rating set"):
            await rating_service.update_rating(
                server.id,
                global_rating.id,
                threshold=30,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_update_global_rating_global_success_and_local_forbidden(self, rating_service, factory, helpers):
        server = await factory.create_server()
        local_game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        local_rating = await rating_service.create_rating(
            server.id,
            local_game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        global_game = await _create_game(factory, rating_service.game_repo)
        global_rating = await rating_service.create_global_rating(global_game.rating_set.id, threshold=5)

        updated = await rating_service.update_global_rating(global_rating.id, threshold=15)
        assert updated.threshold == 15

        with pytest.raises(ForbiddenException, match="Rating set does not belong to a global game"):
            await rating_service.update_global_rating(local_rating.id, threshold=15)

    async def test_delete_rating_forbidden_without_permission(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)

        created = await rating_service.create_rating(
            server.id,
            game.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(ForbiddenException):
            await rating_service.delete_rating(
                server.id,
                created.id,
                permission_mask=helpers.perm_mask(),
            )

    async def test_delete_rating_not_found(self, rating_service, factory, helpers):
        server = await factory.create_server()
        with pytest.raises(NotFoundException):
            await rating_service.delete_rating(
                server.id,
                uuid.uuid4(),
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_delete_rating_wrong_server(self, rating_service, factory, helpers):
        server1 = await factory.create_server()
        server2 = await factory.create_server()
        game1 = await _create_game(factory, rating_service.game_repo, server_id=server1.id)

        created = await rating_service.create_rating(
            server1.id,
            game1.rating_set.id,
            threshold=10,
            icon_id=uuid.uuid4(),
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )

        with pytest.raises(NotFoundException):
            await rating_service.delete_rating(
                server2.id,
                created.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
            )

    async def test_delete_rating_icon(self, rating_service, factory, helpers):
        server = await factory.create_server()
        game = await _create_game(factory, rating_service.game_repo, server_id=server.id)
        icon_id = uuid.uuid4()
        created = await rating_service.create_rating(
            server.id,
            game.rating_set.id,
            threshold=10,
            icon_id=icon_id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert created.icon_id == icon_id

        updated = await rating_service.delete_rating_icon(
            server.id,
            created.id,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_RATING_SET),
        )
        assert updated.icon_id is None
