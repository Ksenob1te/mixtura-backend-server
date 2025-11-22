import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import Game, Server, ServerGame
from src.infra.postgre.repo import GameRepository


@pytest.mark.asyncio(loop_scope="session")
async def test_create_game(async_session):
    repo = GameRepository(async_session)
    g = await repo.create(name="TestGame", icon_url="icon.png", banner_url="banner.png")
    assert g is not None
    assert g.name == "TestGame"
    assert g.icon_url == "icon.png"
    assert g.banner_url == "banner.png"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_game_unique_name(async_session):
    repo = GameRepository(async_session)
    await repo.create("UniqueGame", "i.png", "b.png")
    with pytest.raises(IntegrityError):
        await repo.create("UniqueGame", "i2.png", "b2.png")


@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_id_and_name(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("LookupGame", "i.png", "b.png")
    assert g is not None
    by_id = await repo.get_by_id(g.id)
    assert by_id is not None
    by_name = await repo.get_by_name("LookupGame")
    assert by_name is not None
    assert by_id.id == g.id
    assert by_name.id == g.id
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.get_by_name("Missing") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_update_game(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("UpGame", "i.png", "b.png")
    assert g is not None
    updated = await repo.update(g, name="UpGame2", icon_url="new_icon.png")
    assert updated.name == "UpGame2"
    assert updated.icon_url == "new_icon.png"
    assert updated.banner_url == "b.png"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_game(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("DelGame", "i.png", "b.png")
    assert g is not None
    ok = await repo.delete(g.id)
    assert ok is True
    not_ok = await repo.delete(g.id)
    assert not_ok is False


async def _create_server(session, name="Srv"):
    s = Server(
        name=name,
        owner_id=uuid.uuid4(),
        public=True
    )
    session.add(s)
    await session.flush()
    return s


@pytest.mark.asyncio(loop_scope="session")
async def test_add_and_list_servers(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("LinkGame", "i.png", "b.png")
    s1 = await _create_server(async_session, "S1")
    s2 = await _create_server(async_session, "S2")
    assert g is not None

    await repo.add_to_server(g.id, s1.id)
    await repo.add_to_server(g.id, s2.id)
    # duplicate add should be ignored
    await repo.add_to_server(g.id, s1.id)

    server_ids = await repo.list_servers_for_game(g.id)
    assert set(server_ids) == {s1.id, s2.id}

    res = await async_session.execute(
        select(ServerGame).where(ServerGame.game_id == g.id)
    )
    assert len(res.scalars().all()) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_from_server(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("RemGame", "i.png", "b.png")
    assert g is not None
    s = await _create_server(async_session)
    await repo.add_to_server(g.id, s.id)
    removed = await repo.remove_from_server(g.id, s.id)
    assert removed is True
    removed_again = await repo.remove_from_server(g.id, s.id)
    assert removed_again is False


@pytest.mark.asyncio(loop_scope="session")
async def test_bulk_add_to_server(async_session):
    repo = GameRepository(async_session)
    games = [
        await repo.create(f"BulkGame{i}", "i.png", "b.png")
        for i in range(3)
    ]
    assert all(g is not None for g in games)
    s = await _create_server(async_session)
    await repo.bulk_add_to_server(s.id, [g.id for g in games if g is not None])

    res = await async_session.execute(
        select(ServerGame.server_id, ServerGame.game_id).where(ServerGame.server_id == s.id)
    )
    linked_game_ids = {row.game_id for row in res.all()}
    assert linked_game_ids == {g.id for g in games if g is not None}
