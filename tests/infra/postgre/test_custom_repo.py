import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import Server, Member, Custom, GameRoleSet, RatingSet
from src.infra.postgre.repo import CustomRepository


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


async def _member(session, server: Server):
    m = Member(server_id=server.id, user_id=uuid.uuid4(), name="CustomMember")
    session.add(m)
    await session.flush()
    return m


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_custom(async_session):
    repo = CustomRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    c = await repo.create(member_id=m.id, creator_id=m.id)
    assert c is not None
    assert c.member_id == m.id
    assert c.creator_id == m.id
    by_id = await repo.get_by_id(c.id)
    assert by_id is not None and by_id.id == c.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_member_empty_and_then_populated(async_session):
    repo = CustomRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    assert await repo.list_for_member(m.id) == []
    c1 = await repo.create(m.id)
    c2 = await repo.create(m.id, creator_id=m.id)
    listed = await repo.list_for_member(m.id)
    ids = {x.id for x in listed}
    assert c1 is not None and c2 is not None
    assert ids == {c1.id, c2.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_set_creator_and_unassign(async_session):
    repo = CustomRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    creator = await _member(async_session, s)
    c = await repo.create(m.id)
    assert c is not None and c.creator_id is None
    c = await repo.set_creator(c, creator.id)
    assert c.creator_id == creator.id
    c2 = await repo.set_creator(c, creator.id)
    assert c2.id == c.id and c2.creator_id == creator.id


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_custom(async_session):
    repo = CustomRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    c = await repo.create(m.id)
    assert c is not None
    ok = await repo.delete(c.id)
    assert ok is True
    not_ok = await repo.delete(c.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_multiple_members_isolation(async_session):
    repo = CustomRepository(async_session)
    s = await _server(async_session)
    m1 = await _member(async_session, s)
    m2 = await _member(async_session, s)
    c1 = await repo.create(m1.id)
    c2 = await repo.create(m2.id)
    list1 = await repo.list_for_member(m1.id)
    list2 = await repo.list_for_member(m2.id)
    assert c1 is not None and c2 is not None
    assert {x.id for x in list1} == {c1.id}
    assert {x.id for x in list2} == {c2.id}
