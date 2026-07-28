import uuid

import pytest

from src.core.models.game_role_set import GameRoleSetCreate, GameRoleSetUpdate
from src.infra.postgre.models import Game as GameModel
from src.infra.postgre.repo import GameRoleSetRepository


@pytest.mark.asyncio(loop_scope="session")
class TestGameRoleSetRepository:

    async def test_create_and_get_role_set(self, async_session):
        repo = GameRoleSetRepository(async_session)
        # Bare game with no auto-created role set (factory.create_game builds one
        # for us, but game_id is a unique FK so we cannot attach a second here).
        game = GameModel(id=uuid.uuid4(), name=f"Game-{uuid.uuid4()}")
        async_session.add(game)
        await async_session.flush()

        rs = await repo.create(GameRoleSetCreate(name="SetA", game_id=game.id))
        assert rs is not None
        assert rs.name == "SetA"
        assert rs.game_id == game.id

        by_id = await repo.get(rs.id)
        assert by_id is not None
        assert by_id.id == rs.id
        assert by_id.name == "SetA"

        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_game_id(self, factory):
        repo = GameRoleSetRepository(factory.session)
        game = await factory.create_game()

        role_set = await repo.get_by_game_id(game.id)
        assert role_set is not None
        assert role_set.game_id == game.id

        assert await repo.get_by_game_id(uuid.uuid4()) is None

    async def test_get_detail_returns_nested_game_roles(self, factory):
        repo = GameRoleSetRepository(factory.session)
        game = await factory.create_game()
        role_set = await repo.get_by_game_id(game.id)
        assert role_set is not None

        role_a = await factory.create_game_role(role_set.id, name="Leader")
        role_b = await factory.create_game_role(role_set.id, name="Support")

        detail = await repo.get_detail(role_set.id)
        assert detail is not None
        assert detail.id == role_set.id
        assert detail.game_id == game.id

        role_names = {r.name for r in detail.game_roles}
        assert role_names == {role_a.name, role_b.name}

        assert await repo.get_detail(uuid.uuid4()) is None

    async def test_update_role_set(self, factory):
        repo = GameRoleSetRepository(factory.session)
        game = await factory.create_game()
        role_set = await repo.get_by_game_id(game.id)
        assert role_set is not None

        updated = await repo.update(GameRoleSetUpdate(id=role_set.id, name="Renamed"))
        assert updated.name == "Renamed"
        assert updated.id == role_set.id
        assert updated.game_id == game.id

        fetched = await repo.get(role_set.id)
        assert fetched is not None
        assert fetched.name == "Renamed"

    async def test_delete_role_set(self, factory):
        repo = GameRoleSetRepository(factory.session)
        game = await factory.create_game()
        role_set = await repo.get_by_game_id(game.id)
        assert role_set is not None

        ok = await repo.delete(role_set.id)
        assert ok is True

        assert await repo.get(role_set.id) is None

        not_ok = await repo.delete(role_set.id)
        assert not_ok is False
