import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import Member, Custom, GameRoleSet, GameRole, Server, RatingSet
from src.infra.postgre.repo import CustomRatingRepository


async def _server(session):
    rs = GameRoleSet(name="RS", is_global=False)
    rts = RatingSet(name="RT", min_rating=0, max_rating=50, is_global=False)
    session.add(rs)
    session.add(rts)
    await session.flush()
    s = Server(id=uuid.uuid4(), name="Server", owner_id=uuid.uuid4(), public=False, role_set_id=rs.id, rating_set_id=rts.id)
    session.add(s)
    await session.flush()
    return s


async def _member(session, s: Server):
    m = Member(server_id=s.id, user_id=uuid.uuid4(), server_role_id=None, name="CRMember")
    session.add(m)
    await session.flush()
    return m


async def _custom(session, s: Server):
    m = await _member(session, s)
    c = Custom(member_id=m.id, creator_id=m.id)
    session.add(c)
    await session.flush()
    return c


async def _role(session, name="Role"):
    rs = GameRoleSet(name="Set", is_global=False)
    session.add(rs)
    await session.flush()
    r = GameRole(name=name, role_set_id=rs.id, min_in_team=0, max_in_team=1)
    session.add(r)
    await session.flush()
    return r


@pytest.mark.asyncio(loop_scope="session")
async def test_create_get_and_list(async_session):
    repo = CustomRatingRepository(async_session)
    s = await _server(async_session)
    c = await _custom(async_session, s)
    r = await _role(async_session)
    cr = await repo.create(c.id, r.id, 12)
    assert cr is not None and cr.rating == 12

    by_id = await repo.get_by_id(cr.id)
    assert by_id is not None and by_id.id == cr.id

    by_pair = await repo.get_by_custom_role(c.id, r.id)
    assert by_pair is not None and by_pair.id == cr.id

    list_c = await repo.list_for_custom(c.id)
    assert cr.id in {x.id for x in list_c}


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_pair_constraint(async_session):
    repo = CustomRatingRepository(async_session)
    s = await _server(async_session)
    c = await _custom(async_session, s)
    r = await _role(async_session, name="PairRole")
    await repo.create(c.id, r.id, 1)
    with pytest.raises(IntegrityError):
        await repo.create(c.id, r.id, 2)


@pytest.mark.asyncio(loop_scope="session")
async def test_set_rating_and_delete(async_session):
    repo = CustomRatingRepository(async_session)
    s = await _server(async_session)
    c = await _custom(async_session, s)
    r = await _role(async_session)
    cr = await repo.create(c.id, r.id, 5)
    assert cr is not None

    cr = await repo.set_rating(cr, 7)
    assert cr.rating == 7

    ok = await repo.delete(cr.id)
    assert ok is True
    not_ok = await repo.delete(cr.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_by_pair(async_session):
    repo = CustomRatingRepository(async_session)
    s = await _server(async_session)
    c = await _custom(async_session, s)
    r = await _role(async_session)
    cr = await repo.create(c.id, r.id, 3)
    assert cr is not None

    ok = await repo.delete_by_custom_rating(c.id, r.id)
    assert ok is True
    not_ok = await repo.delete_by_custom_rating(c.id, r.id)
    assert not_ok is False
