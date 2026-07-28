import uuid

import pytest

from src.core.models.game_role import GameRoleCreate, GameRoleUpdate
from src.infra.postgre import IntegrityForeignException
from src.infra.postgre.repo import GameRoleRepository


async def _create_game(factory, session, **kwargs):
    game = await factory.create_game(**kwargs)
    await session.refresh(game, attribute_names=["role_set", "rating_set"])
    return game


@pytest.mark.asyncio(loop_scope="session")
class TestGameRoleRepository:

    async def test_create_and_get_game_role(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game = await _create_game(factory, async_session)
        role = await repo.create(GameRoleCreate(
            name="Support", role_set_id=game.role_set.id, min_in_team=1, max_in_team=3,
            icon_id=uuid.uuid4(), hidden=False,
        ))
        assert role is not None
        assert role.name == "Support"
        by_id = await repo.get(role.id)
        assert by_id is not None and by_id.id == role.id
        assert await repo.get(uuid.uuid4()) is None

    async def test_create_game_role_invalid_role_set(self, async_session):
        repo = GameRoleRepository(async_session)
        invalid_role_set_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.create(GameRoleCreate(
                name="InvalidRole", role_set_id=invalid_role_set_id, min_in_team=1, max_in_team=2,
            ))

    async def test_list_for_set(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game1 = await _create_game(factory, async_session, name="Game1")
        game2 = await _create_game(factory, async_session, name="Game2")
        r1 = await repo.create(GameRoleCreate(name="RoleA", role_set_id=game1.role_set.id, min_in_team=1, max_in_team=2))
        r2 = await repo.create(GameRoleCreate(name="RoleB", role_set_id=game1.role_set.id, min_in_team=2, max_in_team=4))
        r3 = await repo.create(GameRoleCreate(name="RoleC", role_set_id=game2.role_set.id, min_in_team=1, max_in_team=1))
        assert r1 is not None
        assert r2 is not None
        assert r3 is not None
        listed1 = await repo.list_for_set(game1.role_set.id)
        listed2 = await repo.list_for_set(game2.role_set.id)
        assert {r.id for r in listed1} == {r1.id, r2.id}
        assert {r.id for r in listed2} == {r3.id}

    async def test_setters_update_fields(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game = await _create_game(factory, async_session)
        role = await repo.create(GameRoleCreate(name="RoleX", role_set_id=game.role_set.id, min_in_team=1, max_in_team=2))
        assert role is not None
        role = await repo.update(GameRoleUpdate(id=role.id, name="RoleY"))
        assert role.name == "RoleY"
        new_icon_id = uuid.uuid4()
        role = await repo.update(GameRoleUpdate(id=role.id, icon_id=new_icon_id))
        assert role.icon_id == new_icon_id
        role = await repo.update(GameRoleUpdate(id=role.id, hidden=True))
        assert role.hidden is True
        role = await repo.update(GameRoleUpdate(id=role.id, min_in_team=1, max_in_team=5))
        assert role.min_in_team == 1 and role.max_in_team == 5
        role = await repo.update(GameRoleUpdate(id=role.id, min_in_team=4))
        assert role.min_in_team == 4 and role.max_in_team == 5
        role = await repo.update(GameRoleUpdate(id=role.id, max_in_team=4))
        assert role.max_in_team == 4

    async def test_delete_game_role(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game = await _create_game(factory, async_session)
        role = await repo.create(GameRoleCreate(name="DeleteMe", role_set_id=game.role_set.id, min_in_team=1, max_in_team=1))
        assert role is not None
        ok = await repo.delete(role.id)
        assert ok is True
        not_ok = await repo.delete(role.id)
        assert not_ok is False

    async def test_list_for_set_empty(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game = await _create_game(factory, async_session)
        listed = await repo.list_for_set(game.role_set.id)
        assert listed == []

    async def test_copy_game_role(self, async_session, factory):
        repo = GameRoleRepository(async_session)
        game1 = await _create_game(factory, async_session, name="SourceGame")
        game2 = await _create_game(factory, async_session, name="TargetGame")
        role = await repo.create(GameRoleCreate(
            name="OriginalRole", role_set_id=game1.role_set.id, min_in_team=1, max_in_team=3,
            icon_id=uuid.uuid4(), hidden=False,
        ))
        assert role is not None
        copied_role = await repo.copy_role(role, game2.role_set.id)
        assert copied_role is not None
        assert copied_role.id != role.id
        assert copied_role.name == role.name
        assert copied_role.min_in_team == role.min_in_team
        assert copied_role.max_in_team == role.max_in_team
        assert copied_role.icon_id == role.icon_id
        assert copied_role.hidden == role.hidden
        assert copied_role.role_set_id == game2.role_set.id
