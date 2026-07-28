import uuid

import pytest
from sqlalchemy import select

from src.core.models.game import GameCreate, GameUpdate
from src.infra.postgre import IntegrityForeignException, IntegrityUniqueException
from src.infra.postgre.models import ServerGame
from src.infra.postgre.repo import GameRepository


@pytest.mark.asyncio(loop_scope="session")
class TestGameRepository:
    async def test_create_and_get_global_game(self, async_session):
        repo = GameRepository(async_session)
        icon_id = uuid.uuid4()
        banner_id = uuid.uuid4()
        g = await repo.create(GameCreate(name="TestGame", icon_id=icon_id, banner_id=banner_id))
        assert g is not None
        assert g.name == "TestGame"
        assert g.icon_id == icon_id
        assert g.banner_id == banner_id
        assert g.server_id is None
        assert g.is_global is True

        by_id = await repo.get(g.id)
        assert by_id is not None
        assert by_id.id == g.id
        assert await repo.get(uuid.uuid4()) is None

    async def test_create_and_get_local_game(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        g = await repo.create(GameCreate(name="LocalGame", server_id=s.id))
        assert g is not None
        assert g.server_id == s.id
        assert g.is_global is False

        by_id = await repo.get(g.id)
        assert by_id is not None
        assert by_id.server_id == s.id

    async def test_create_local_game_unreal_server(self, async_session):
        repo = GameRepository(async_session)
        with pytest.raises(IntegrityForeignException):
            await repo.create(GameCreate(name="OrphanGame", server_id=uuid.uuid4()))

    async def test_update_game(self, async_session):
        repo = GameRepository(async_session)
        icon_id = uuid.uuid4()
        banner_id = uuid.uuid4()
        g = await repo.create(GameCreate(name="UpdGame", icon_id=icon_id, banner_id=banner_id))
        assert g is not None

        updated = await repo.update(GameUpdate(id=g.id, name="UpdGame2"))
        assert updated.name == "UpdGame2"
        assert updated.icon_id == icon_id
        assert updated.banner_id == banner_id

        updated2 = await repo.update(GameUpdate(id=g.id, icon_id=None))
        assert updated2.icon_id is None
        assert updated2.banner_id == banner_id
        assert updated2.name == "UpdGame2"

    async def test_get_by_name_scoping(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        global_game = await repo.create(GameCreate(name="SharedName"))
        local_game = await repo.create(GameCreate(name="SharedName", server_id=s.id))

        by_default = await repo.get_by_name("SharedName")
        assert by_default is not None
        assert by_default.id == global_game.id

        by_server = await repo.get_by_name("SharedName", server_id=s.id)
        assert by_server is not None
        assert by_server.id == local_game.id

        assert await repo.get_by_name("Missing") is None
        assert await repo.get_by_name("SharedName", server_id=uuid.uuid4()) is None

    async def test_two_global_games_same_name_raises(self, async_session):
        repo = GameRepository(async_session)
        await repo.create(GameCreate(name="UniqueGlobal"))
        with pytest.raises(IntegrityUniqueException):
            await repo.create(GameCreate(name="UniqueGlobal"))

    async def test_two_servers_can_share_local_game_name(self, async_session, factory):
        repo = GameRepository(async_session)
        s1 = await factory.create_server()
        s2 = await factory.create_server()

        g1 = await repo.create(GameCreate(name="SameLocalName", server_id=s1.id))
        g2 = await repo.create(GameCreate(name="SameLocalName", server_id=s2.id))
        assert g1.id != g2.id
        assert g1.server_id == s1.id
        assert g2.server_id == s2.id

    async def test_same_server_duplicate_local_name_raises(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        await repo.create(GameCreate(name="DupLocalName", server_id=s.id))
        with pytest.raises(IntegrityUniqueException):
            await repo.create(GameCreate(name="DupLocalName", server_id=s.id))

    async def test_get_detail_returns_nested_sets(self, async_session, factory):
        repo = GameRepository(async_session)
        g = await factory.create_game(name="DetailGame", min_rating=5, max_rating=95)

        detail = await repo.get_detail(g.id)
        assert detail is not None
        assert detail.id == g.id
        assert detail.role_set.game_id == g.id
        assert detail.role_set.game_roles == []
        assert detail.rating_set.game_id == g.id
        assert detail.rating_set.min_rating == 5
        assert detail.rating_set.max_rating == 95
        assert detail.rating_set.ratings == []

        assert await repo.get_detail(uuid.uuid4()) is None

    async def test_list_global_excludes_local_games(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        global_game = await factory.create_game(name="GlobalListed")
        local_game = await factory.create_game(name="LocalListed", server_id=s.id)

        globals_ = await repo.list_global()
        global_ids = {item.id for item in globals_}
        assert global_game.id in global_ids
        assert local_game.id not in global_ids

    async def test_list_owned_by_server(self, async_session, factory):
        repo = GameRepository(async_session)
        s1 = await factory.create_server()
        s2 = await factory.create_server()
        owned_by_s1 = await factory.create_game(name="OwnedByS1", server_id=s1.id)
        await factory.create_game(name="OwnedByS2", server_id=s2.id)

        owned = await repo.list_owned_by_server(s1.id)
        owned_ids = {item.id for item in owned}
        assert owned_ids == {owned_by_s1.id}

    async def test_list_for_server(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        other_s = await factory.create_server()
        attached_game = await factory.create_game(name="AttachedGame")
        unattached_game = await factory.create_game(name="UnattachedGame")
        await factory.attach_game(s.id, attached_game.id)

        listed = await repo.list_for_server(s.id)
        listed_ids = {item.id for item in listed}
        assert attached_game.id in listed_ids
        assert unattached_game.id not in listed_ids

        listed_item = next(item for item in listed if item.id == attached_game.id)
        assert listed_item.role_set.game_id == attached_game.id
        assert listed_item.rating_set.game_id == attached_game.id

        assert await repo.list_for_server(other_s.id) == []

    async def test_is_enabled_on_server(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        g = await factory.create_game(name="EnableCheckGame")

        assert await repo.is_enabled_on_server(s.id, g.id) is False

        await factory.attach_game(s.id, g.id)
        assert await repo.is_enabled_on_server(s.id, g.id) is True

        await repo.remove_from_server(g.id, s.id)
        assert await repo.is_enabled_on_server(s.id, g.id) is False

    async def test_add_and_list_servers(self, async_session, factory):
        repo = GameRepository(async_session)
        g = await repo.create(GameCreate(name="LinkGame"))
        s1 = await factory.create_server()
        s2 = await factory.create_server()
        assert g is not None

        await repo.add_to_server(g.id, s1.id)
        await repo.add_to_server(g.id, s2.id)
        await repo.add_to_server(g.id, s1.id)

        res = await async_session.execute(
            select(ServerGame).where(ServerGame.game_id == g.id)
        )
        assert len(res.scalars().all()) == 2

    async def test_add_to_server_non_existing_server(self, async_session):
        repo = GameRepository(async_session)
        g = await repo.create(GameCreate(name="NonExistServerGame"))
        assert g is not None
        non_existing_server_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.add_to_server(g.id, non_existing_server_id)

    async def test_remove_from_server(self, async_session, factory):
        repo = GameRepository(async_session)
        g = await repo.create(GameCreate(name="RemGame"))
        assert g is not None
        s = await factory.create_server()
        await repo.add_to_server(g.id, s.id)
        removed = await repo.remove_from_server(g.id, s.id)
        assert removed is True
        removed_again = await repo.remove_from_server(g.id, s.id)
        assert removed_again is False

    async def test_bulk_add_to_server(self, async_session, factory):
        repo = GameRepository(async_session)
        games = [
            await repo.create(GameCreate(name=f"BulkGame{i}"))
            for i in range(3)
        ]
        assert all(g is not None for g in games)
        s = await factory.create_server()
        await repo.bulk_add_to_server(s.id, [g.id for g in games if g is not None])

        res = await async_session.execute(
            select(ServerGame.server_id, ServerGame.game_id).where(ServerGame.server_id == s.id)
        )
        linked_game_ids = {row.game_id for row in res.all()}
        assert linked_game_ids == {g.id for g in games if g is not None}

    async def test_bulk_remove_from_server(self, async_session, factory):
        repo = GameRepository(async_session)
        games = [
            await repo.create(GameCreate(name=f"BulkRemGame{i}"))
            for i in range(3)
        ]
        s = await factory.create_server()
        await repo.bulk_add_to_server(s.id, [g.id for g in games])

        # Remove first two
        count = await repo.bulk_remove_from_server(s.id, [games[0].id, games[1].id])
        assert count == 2

        res = await async_session.execute(
            select(ServerGame.game_id).where(ServerGame.server_id == s.id)
        )
        remaining = res.scalars().all()
        assert len(remaining) == 1
        assert remaining[0] == games[2].id

    async def test_set_server_games(self, async_session, factory):
        repo = GameRepository(async_session)
        g1 = await repo.create(GameCreate(name="SetGame1"))
        g2 = await repo.create(GameCreate(name="SetGame2"))
        g3 = await repo.create(GameCreate(name="SetGame3"))
        s = await factory.create_server()

        # Initial set: g1, g2
        await repo.set_server_games(s.id, [g1.id, g2.id])

        res = await async_session.execute(
            select(ServerGame.game_id).where(ServerGame.server_id == s.id)
        )
        current = set(res.scalars().all())
        assert current == {g1.id, g2.id}

        # Update set: g2, g3 (g1 removed, g3 added, g2 kept)
        await repo.set_server_games(s.id, [g2.id, g3.id])

        res = await async_session.execute(
            select(ServerGame.game_id).where(ServerGame.server_id == s.id)
        )
        current = set(res.scalars().all())
        assert current == {g2.id, g3.id}

    async def test_delete_game(self, async_session):
        repo = GameRepository(async_session)
        g = await repo.create(GameCreate(name="DelGame"))
        assert g is not None
        ok = await repo.delete(g.id)
        assert ok is True
        not_ok = await repo.delete(g.id)
        assert not_ok is False

    async def test_add_non_existing_game(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        non_existing_game_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.add_to_server(non_existing_game_id, s.id)

    async def test_add_bulk_non_existing_game(self, async_session, factory):
        repo = GameRepository(async_session)
        s = await factory.create_server()
        non_existing_game_ids = [uuid.uuid4() for _ in range(3)]
        with pytest.raises(IntegrityForeignException):
            await repo.bulk_add_to_server(s.id, non_existing_game_ids)
