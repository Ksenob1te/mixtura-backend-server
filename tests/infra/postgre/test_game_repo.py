import uuid
import pytest
from sqlalchemy import select

from src.infra.postgre.models import ServerGame
from src.infra.postgre.repo import GameRepository
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException


@pytest.mark.asyncio(loop_scope="session")
class TestGameRepository:
    async def test_create_game(self, async_session):
        repo = GameRepository(async_session)
        icon_id = uuid.uuid4()
        banner_id = uuid.uuid4()
        g = await repo.create(name="TestGame", icon_id=icon_id, banner_id=banner_id)
        assert g is not None
        assert g.name == "TestGame"
        assert g.icon_id == icon_id
        assert g.banner_id == banner_id

    async def test_create_game_unique_name(self, async_session):
        repo = GameRepository(async_session)
        await repo.create("UniqueGame", uuid.uuid4(), uuid.uuid4())
        with pytest.raises(IntegrityUniqueException):
            await repo.create("UniqueGame", uuid.uuid4(), uuid.uuid4())

    async def test_get_by_id_and_name(self, async_session):
        repo = GameRepository(async_session)
        g = await repo.create("LookupGame", uuid.uuid4(), uuid.uuid4())
        assert g is not None
        by_id = await repo.get_by_id(g.id)
        assert by_id is not None
        by_name = await repo.get_by_name("LookupGame")
        assert by_name is not None
        assert by_id.id == g.id
        assert by_name.id == g.id
        assert await repo.get_by_id(uuid.uuid4()) is None
        assert await repo.get_by_name("Missing") is None

    async def test_setters_modify_fields(self, async_session):
        repo = GameRepository(async_session)
        g = await repo.create("SetterGame", uuid.uuid4(), uuid.uuid4())
        assert g is not None
        g = await repo.set_name(g, "SetterGame2")
        assert g.name == "SetterGame2"
        new_icon_id = uuid.uuid4()
        g = await repo.set_icon(g, new_icon_id)
        assert g.icon_id == new_icon_id
        new_banner_id = uuid.uuid4()
        g = await repo.set_banner(g, new_banner_id)
        assert g.banner_id == new_banner_id

    async def test_delete_game(self, async_session):
        repo = GameRepository(async_session)
        g = await repo.create("DelGame", uuid.uuid4(), uuid.uuid4())
        assert g is not None
        ok = await repo.delete(g.id)
        assert ok is True
        not_ok = await repo.delete(g.id)
        assert not_ok is False

    async def test_add_and_list_servers(self, async_session, factory):
        repo = GameRepository(async_session)
        g = await repo.create("LinkGame", uuid.uuid4(), uuid.uuid4())
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
        g = await repo.create("NonExistServerGame", uuid.uuid4(), uuid.uuid4())
        assert g is not None
        non_existing_server_id = uuid.uuid4()
        with pytest.raises(IntegrityForeignException):
            await repo.add_to_server(g.id, non_existing_server_id)

    async def test_remove_from_server(self, async_session, factory):
        repo = GameRepository(async_session)
        g = await repo.create("RemGame", uuid.uuid4(), uuid.uuid4())
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
            await repo.create(f"BulkGame{i}", uuid.uuid4(), uuid.uuid4())
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
            await repo.create(f"BulkRemGame{i}", uuid.uuid4(), uuid.uuid4())
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
        g1 = await repo.create("SetGame1", uuid.uuid4(), uuid.uuid4())
        g2 = await repo.create("SetGame2", uuid.uuid4(), uuid.uuid4())
        g3 = await repo.create("SetGame3", uuid.uuid4(), uuid.uuid4())
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

    async def test_get_all_games(self, async_session):
        repo = GameRepository(async_session)
        g1 = await repo.create("AllGame1", uuid.uuid4(), uuid.uuid4())
        g2 = await repo.create("AllGame2", uuid.uuid4(), uuid.uuid4())
        all_games = await repo.get_all()
        all_game_ids = {g.id for g in all_games}
        assert g1 is not None and g2 is not None
        assert g1.id in all_game_ids
        assert g2.id in all_game_ids

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

