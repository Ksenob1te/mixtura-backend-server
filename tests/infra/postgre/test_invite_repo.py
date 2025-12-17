import uuid
import pytest
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException, IntegrityUnknownException

from src.infra.postgre.models import Server, Member, GameRoleSet, RatingSet
from src.infra.postgre.repo import InviteRepository


async def _server(session, name="Srv"):
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=100, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(name=name, owner_id=uuid.uuid4(), public=True, role_set_id=rs.id, rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _member(session, server: Server):
    m = Member(server_id=server.id, user_id=uuid.uuid4(), name="Member")
    session.add(m)
    await session.flush()
    return m


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_invite(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    inviter = await _member(async_session, s)
    inv = await repo.create(server_id=s.id, use_limit=5, inviter_id=inviter.id)
    assert inv is not None
    by_id = await repo.get_by_id(inv.id)
    assert by_id is not None and by_id.id == inv.id
    by_key = await repo.get_by_key(inv.key)
    assert by_key is not None and by_key.id == inv.id
    assert await repo.get_by_key("missing-key") is None
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_invite_unreal_server(async_session):
    repo = InviteRepository(async_session)
    unreal_server_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create(server_id=unreal_server_id, use_limit=5)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_with_custom_key_and_uniqueness(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    inv1 = await repo.create(server_id=s.id, use_limit=1, key="CUSTOMKEY")
    assert inv1 is not None and inv1.key == "CUSTOMKEY"
    with pytest.raises(IntegrityUniqueException):
        await repo.create(server_id=s.id, use_limit=2, key="CUSTOMKEY")


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_server(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    invites = [await repo.create(server_id=s.id, use_limit=i + 1) for i in range(3)]
    listed = await repo.list_for_server(s.id)
    assert {i.id for i in listed} == {i.id for i in invites if i is not None}


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_invite(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    inv = await repo.create(server_id=s.id, use_limit=10)
    assert inv is not None
    ok = await repo.delete(inv.id)
    assert ok is True
    not_ok = await repo.delete(inv.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_generate_unique_keys(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    keys = set()
    for _ in range(1000):
        inv = await repo.create(server_id=s.id, use_limit=1)
        assert inv is not None
        assert inv.key not in keys
        keys.add(inv.key)


@pytest.mark.asyncio(loop_scope="session")
async def test_set_use_limit_and_decrement(async_session):
    repo = InviteRepository(async_session)
    s = await _server(async_session)
    inv = await repo.create(server_id=s.id, use_limit=3)
    assert inv is not None and inv.use_limit == 3
    inv = await repo.decrement_use_limit(inv)
    assert inv.use_limit == 2
    inv = await repo.decrement_use_limit(inv)
    inv = await repo.decrement_use_limit(inv)
    assert inv.use_limit == 0
    inv = await repo.decrement_use_limit(inv)
    assert inv.use_limit == 0
    inv = await repo.set_use_limit(inv, 10)
    assert inv.use_limit == 10
    inv = await repo.set_use_limit(inv, -5)
    assert inv.use_limit == 0
