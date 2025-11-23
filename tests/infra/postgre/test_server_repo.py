import uuid
import pytest

from src.infra.postgre.repo import ServerRepository, GameRoleSetRepository, RatingSetRepository
from src.infra.postgre.models import GameRoleSet, RatingSet


async def _role_set(session, name="RS"):
    rs = GameRoleSet(name=name, is_global=False)
    session.add(rs)
    await session.flush()
    return rs


async def _rating_set(session, name="RT", min_rating=0, max_rating=100):
    rts = RatingSet(name=name, min_rating=min_rating, max_rating=max_rating, is_global=False)
    session.add(rts)
    await session.flush()
    return rts


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_server(async_session):
    repo = ServerRepository(async_session)
    rs = await _role_set(async_session)
    rts = await _rating_set(async_session)
    s = await repo.create(name="Srv1", owner_id=uuid.uuid4(), role_set_id=rs.id, rating_set_id=rts.id,
                          public=False,
                          description="desc", icon_url="i.png", banner_url="b.png")
    assert s is not None
    assert s.name == "Srv1"
    assert s.public is False
    assert s.description == "desc"
    assert s.icon_url == "i.png"
    assert s.banner_url == "b.png"
    assert s.role_set_id == rs.id
    assert s.rating_set_id == rts.id
    by_id = await repo.get_by_id(s.id)
    assert by_id is not None and by_id.id == s.id


@pytest.mark.asyncio(loop_scope="session")
async def test_setters_update_fields(async_session):
    repo = ServerRepository(async_session)
    rs = await _role_set(async_session)
    rts = await _rating_set(async_session)
    s = await repo.create(name="Srv2", owner_id=uuid.uuid4(), role_set_id=rs.id, rating_set_id=rts.id)
    assert s is not None
    s = await repo.set_name(s, "Srv2-Updated")
    assert s.name == "Srv2-Updated"
    s = await repo.set_description(s, "NewDesc")
    assert s.description == "NewDesc"
    s = await repo.set_public(s, True)
    assert s.public is True
    new_icon_id = uuid.uuid4()
    s = await repo.set_icon(s, "icon2.png", new_icon_id)
    assert s.icon_url == "icon2.png" and s.icon_id == new_icon_id
    new_banner_id = uuid.uuid4()
    s = await repo.set_banner(s, "banner2.png", new_banner_id)
    assert s.banner_url == "banner2.png" and s.banner_id == new_banner_id


@pytest.mark.asyncio(loop_scope="session")
async def test_list_and_delete_server(async_session):
    repo = ServerRepository(async_session)
    rs = await _role_set(async_session)
    rts = await _rating_set(async_session)
    owner = uuid.uuid4()
    s1 = await repo.create(name="PubSrv", owner_id=owner, role_set_id=rs.id, rating_set_id=rts.id, public=True)
    s2 = await repo.create(name="PrivSrv", owner_id=owner, role_set_id=rs.id, rating_set_id=rts.id, public=False)
    assert s1 is not None and s2 is not None

    by_owner = await repo.list_by_owner(owner)
    assert {s.id for s in by_owner} == {s1.id, s2.id}

    public_list = await repo.list_public()
    assert s1.id in {s.id for s in public_list}

    ok = await repo.delete(s2.id)
    assert ok is True
    not_ok = await repo.delete(s2.id)
    assert not_ok is False
