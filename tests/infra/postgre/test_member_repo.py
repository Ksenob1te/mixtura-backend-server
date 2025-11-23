import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import Server, Member, ServerRole, GameRoleSet, RatingSet
from src.infra.postgre.repo import MemberRepository


async def _server(session, name="Srv"):
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(name=name, owner_id=uuid.uuid4(), public=True, role_set_id=rs.id, rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _role(session, server: Server, name="Role", position=0):
    r = ServerRole(server_id=server.id, name=name, position=position)
    session.add(r)
    await session.flush()
    return r


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_member(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4())
    assert m is not None
    by_id = await repo.get_by_id(m.id)
    assert by_id is not None and by_id.id == m.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_duplicate_user_membership_raises(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    user_id = uuid.uuid4()
    _ = await repo.create(server_id=s.id, user_id=user_id)
    with pytest.raises(IntegrityError):
        await repo.create(server_id=s.id, user_id=user_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_and_list_active(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    members = [await repo.create(server_id=s.id, user_id=uuid.uuid4()) for _ in range(3)]
    listed = await repo.list_for_server(s.id)
    assert {m.id for m in listed} == {m.id for m in members if m is not None}
    active_listed = await repo.list_active_for_server(s.id)
    assert {m.id for m in active_listed} == {m.id for m in members if m is not None}


@pytest.mark.asyncio(loop_scope="session")
async def test_activation_and_deactivation(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4())
    assert m is not None and m.active is True
    m = await repo.deactivate(m)
    assert m.active is False
    m2 = await repo.deactivate(m)
    assert m2.id == m.id and m2.active is False
    m = await repo.activate(m)
    assert m.active is True
    m2 = await repo.activate(m)
    assert m2.id == m.id and m2.active is True


@pytest.mark.asyncio(loop_scope="session")
async def test_set_role(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    role = await _role(async_session, s)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4())
    assert m is not None
    m = await repo.set_role(m, role.id)
    assert m.server_role_id == role.id
    m2 = await repo.set_role(m, role.id)
    assert m2.id == m.id and m2.server_role_id == role.id
    m = await repo.set_role(m, None)
    assert m.server_role_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_member(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    m = await repo.create(server_id=s.id, user_id=uuid.uuid4())
    assert m is not None
    ok = await repo.delete(m.id)
    assert ok is True
    not_ok = await repo.delete(m.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_anonymous_members_allowed(async_session):
    repo = MemberRepository(async_session)
    s = await _server(async_session)
    anon_members = [await repo.create(server_id=s.id, user_id=None) for _ in range(5)]
    assert all(m is not None for m in anon_members)
    assert all(m.user_id is None for m in anon_members if m is not None)
    ids = {m.id for m in anon_members if m is not None}
    assert len(ids) == len(anon_members)
    listed = await repo.list_for_server(s.id)
    assert ids.issubset({m.id for m in listed})
