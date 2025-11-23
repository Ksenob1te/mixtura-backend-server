import uuid
from datetime import datetime, timedelta, timezone
import pytest

from src.infra.postgre.models import Server, Member, GameRoleSet, RatingSet
from src.infra.postgre.repo import RestrictionRepository, MemberRepository


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
    m = Member(server_id=server.id, user_id=uuid.uuid4(), name="RestrictMember")
    session.add(m)
    await session.flush()
    return m


@pytest.mark.asyncio(loop_scope="session")
async def test_create_get_and_list(async_session):
    repo = RestrictionRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    r1 = await repo.create(m.id, "Reason1", datetime.now(timezone.utc) + timedelta(hours=1), "TYPE_A")
    r2 = await repo.create(m.id, "Reason2", datetime.now(timezone.utc) + timedelta(hours=2), "TYPE_B")
    assert r1 is not None and r2 is not None
    by_id = await repo.get_by_id(r1.id)
    assert by_id is not None and by_id.id == r1.id
    listed = await repo.list_for_member(m.id)
    assert {r.id for r in listed} == {r1.id, r2.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_list_active_filters_expired(async_session):
    repo = RestrictionRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    active = await repo.create(m.id, "Active", datetime.now(timezone.utc) + timedelta(minutes=30), "ACTIVE")
    expired = await repo.create(m.id, "Expired", datetime.now(timezone.utc) - timedelta(minutes=5), "EXPIRED")
    assert active is not None and expired is not None
    listed_active = await repo.list_active_for_member(m.id)
    assert {r.id for r in listed_active} == {active.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_setters_update_fields(async_session):
    repo = RestrictionRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    r = await repo.create(m.id, "Initial", datetime.now(timezone.utc) + timedelta(minutes=10), "INIT")
    assert r is not None
    r = await repo.set_reason(r, "UpdatedReason")
    assert r.reason == "UpdatedReason"
    new_exp = datetime.now(timezone.utc) + timedelta(hours=2)
    r = await repo.set_expiration(r, new_exp)
    assert r.expiration_date == new_exp
    r = await repo.set_type_code(r, "NEWTYPE")
    assert r.type_code == "NEWTYPE"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_restriction(async_session):
    repo = RestrictionRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    r = await repo.create(m.id, "Del", datetime.now(timezone.utc) + timedelta(minutes=5), "DEL")
    assert r is not None
    ok = await repo.delete(r.id)
    assert ok is True
    not_ok = await repo.delete(r.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_active_with_now_override(async_session):
    repo = RestrictionRepository(async_session)
    s = await _server(async_session)
    m = await _member(async_session, s)
    future_exp = datetime.now(timezone.utc) + timedelta(minutes=20)
    r = await repo.create(m.id, "Future", future_exp, "FUT")
    assert r is not None
    override_now = future_exp + timedelta(minutes=1)
    listed = await repo.list_active_for_member(m.id, now=override_now)
    assert listed == []
