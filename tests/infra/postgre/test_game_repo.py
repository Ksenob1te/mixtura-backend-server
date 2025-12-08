import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import Game, Server, ServerGame, GameRoleSet, RatingSet
from src.infra.postgre.repo import GameRepository


async def _create_server(session, name="Srv"):
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=10, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(name=name, owner_id=uuid.uuid4(), public=True, role_set_id=rs.id, rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


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
async def test_setters_modify_fields(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("SetterGame", "i.png", "b.png")
    assert g is not None
    g = await repo.set_name(g, "SetterGame2")
    assert g.name == "SetterGame2"
    g = await repo.set_icon(g, "new_icon.png")
    assert g.icon_url == "new_icon.png"
    g = await repo.set_banner(g, "new_banner.png")
    assert g.banner_url == "new_banner.png"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_game(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("DelGame", "i.png", "b.png")
    assert g is not None
    ok = await repo.delete(g.id)
    assert ok is True
    not_ok = await repo.delete(g.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_add_and_list_servers(async_session):
    repo = GameRepository(async_session)
    g = await repo.create("LinkGame", "i.png", "b.png")
    s1 = await _create_server(async_session, "S1")
    s2 = await _create_server(async_session, "S2")
    assert g is not None

    await repo.add_to_server(g.id, s1.id)
    await repo.add_to_server(g.id, s2.id)
    await repo.add_to_server(g.id, s1.id)

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


@pytest.mark.asyncio(loop_scope="session")
async def test_get_all_games(async_session):
    repo = GameRepository(async_session)
    g1 = await repo.create("AllGame1", "i1.png", "b1.png")
    g2 = await repo.create("AllGame2", "i2.png", "b2.png")
    all_games = await repo.get_all()
    all_game_ids = {g.id for g in all_games}
    assert g1 is not None and g2 is not None
    assert g1.id in all_game_ids
    assert g2.id in all_game_ids


@pytest.mark.asyncio(loop_scope="session")
async def test_add_non_existing_game(async_session):
    repo = GameRepository(async_session)
    s = await _create_server(async_session)
    non_existing_game_id = uuid.uuid4()
    with pytest.raises(IntegrityError):
        await repo.add_to_server(non_existing_game_id, s.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_add_bulk_non_existing_game(async_session):
    repo = GameRepository(async_session)
    s = await _create_server(async_session)
    non_existing_game_ids = [uuid.uuid4() for _ in range(3)]
    with pytest.raises(IntegrityError):
        await repo.bulk_add_to_server(s.id, non_existing_game_ids)

