import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from src.core.models.game_role import GameRoleCreate
from src.core.models.rating import RatingCreate
from src.core.services.game import GameService
from src.infra.postgre.models import GameRoleSet as GameRoleSetModel
from src.infra.postgre.models import RatingSet as RatingSetModel
from src.infra.postgre.repo import (
    GameRepository,
    GameRoleRepository,
    GameRoleSetRepository,
    RatingRepository,
    RatingSetRepository,
    ServerRepository,
)
from src.infra.postgre.static import PERMISSION


@pytest_asyncio.fixture(loop_scope="session")
async def game_service(async_session):
    return GameService(
        game_repo=GameRepository(async_session),
        server_repo=ServerRepository(async_session),
        game_role_set_repo=GameRoleSetRepository(async_session),
        rating_set_repo=RatingSetRepository(async_session),
        game_role_repo=GameRoleRepository(async_session),
        rating_repo=RatingRepository(async_session),
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

    async def test_add_games_to_server_raises_when_game_belongs_to_other_server(
        self, game_service, factory, helpers
    ):
        server = await factory.create_server()
        own_game = await factory.create_game(name="Own")

        other_server = await factory.create_server()
        other_local_game = await factory.create_game(name="OtherLocal", server_id=other_server.id)

        with pytest.raises(NotFoundException):
            await game_service.add_games_to_server(
                server.id,
                [own_game.id, other_local_game.id],
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

    async def test_create_global_game_raises_when_bounds_invalid(self, game_service):
        with pytest.raises(BadRequestException):
            await game_service.create_global_game("BadGame", 100, 0)

    async def test_create_local_game_forbidden_without_permission(self, game_service, factory, helpers):
        server = await factory.create_server()

        with pytest.raises(ForbiddenException):
            await game_service.create_local_game(
                server.id, "Chess", 0, 100,
                permission_mask=helpers.perm_mask(),
            )

    async def test_create_local_game_success(self, game_service, factory, helpers):
        server = await factory.create_server()

        detail = await game_service.create_local_game(
            server.id, "Chess", 0, 100,
            permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
        )

        assert detail.server_id == server.id
        assert detail.is_global is False
        assert len(detail.role_set.game_roles) == 1
        assert detail.role_set.game_roles[0].name == "Leader"
        assert detail.role_set.game_roles[0].min_in_team == 1
        assert detail.role_set.game_roles[0].max_in_team == 1
        assert detail.rating_set.min_rating == 0
        assert detail.rating_set.max_rating == 100

        server_games = await game_service.list_server_games(server.id)
        assert detail.id in {g.id for g in server_games}

    async def test_copy_global_game_copies_roles_and_ratings(self, game_service, factory, helpers):
        global_game = await factory.create_game(name="Global", min_rating=0, max_rating=200)
        role_set_id = await game_service.game_repo._session.scalar(
            select(GameRoleSetModel.id).where(GameRoleSetModel.game_id == global_game.id)
        )
        rating_set_id = await game_service.game_repo._session.scalar(
            select(RatingSetModel.id).where(RatingSetModel.game_id == global_game.id)
        )
        await game_service.game_role_repo.create(
            GameRoleCreate(name="Tank", role_set_id=role_set_id, min_in_team=1, max_in_team=2)
        )
        await game_service.game_role_repo.create(
            GameRoleCreate(name="Healer", role_set_id=role_set_id, min_in_team=0, max_in_team=1)
        )
        await game_service.rating_repo.create(
            RatingCreate(rating_set_id=rating_set_id, threshold=10)
        )
        await game_service.rating_repo.create(
            RatingCreate(rating_set_id=rating_set_id, threshold=50)
        )

        # Freshly-created child rows are not reflected on an already-identity-mapped
        # parent's eagerly-loaded collection until that attribute is expired.
        rating_set_obj = await game_service.game_repo._session.get(RatingSetModel, rating_set_id)
        game_service.game_repo._session.expire(rating_set_obj, ["ratings"])

        server = await factory.create_server()
        copy = await game_service.copy_global_game(
            server.id, global_game.id, permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME)
        )

        assert copy.id != global_game.id
        assert copy.server_id == server.id
        assert copy.is_global is False
        assert copy.name == global_game.name
        assert len(copy.role_set.game_roles) == 2
        assert {r.name for r in copy.role_set.game_roles} == {"Tank", "Healer"}
        assert len(copy.rating_set.ratings) == 2
        assert {r.threshold for r in copy.rating_set.ratings} == {10, 50}

        source_detail = await game_service.game_repo.get_detail(global_game.id)
        assert source_detail is not None
        assert source_detail.server_id is None
        assert len(source_detail.role_set.game_roles) == 2
        assert len(source_detail.rating_set.ratings) == 2

    async def test_copy_global_game_raises_when_source_not_global(self, game_service, factory, helpers):
        owner_server = await factory.create_server()
        local_game = await factory.create_game(name="Local", server_id=owner_server.id)

        other_server = await factory.create_server()
        with pytest.raises(ForbiddenException):
            await game_service.copy_global_game(
                other_server.id, local_game.id, permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME)
            )

    async def test_update_local_game_raises_forbidden_for_global_game(self, game_service, factory, helpers):
        server = await factory.create_server()
        global_game = await factory.create_game(name="Global")

        with pytest.raises(ForbiddenException):
            await game_service.update_local_game(
                server.id, global_game.id, name="Renamed",
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )

    async def test_delete_local_game_raises_forbidden_for_global_game(self, game_service, factory, helpers):
        server = await factory.create_server()
        global_game = await factory.create_game(name="Global")

        with pytest.raises(ForbiddenException):
            await game_service.delete_local_game(
                server.id, global_game.id,
                permission_mask=helpers.perm_mask(PERMISSION.EDIT_SERVER_GAME),
            )
