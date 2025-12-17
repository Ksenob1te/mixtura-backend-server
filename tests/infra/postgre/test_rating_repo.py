import uuid
import pytest

from src.infra.postgre.models import RatingSet, Rating
from src.infra.postgre.repo import RatingRepository

from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException


async def _create_rating_set(session, name="Set", min_rating=0, max_rating=500, is_global=False):
    rs = RatingSet(
        name=name,
        min_rating=min_rating,
        max_rating=max_rating,
        is_global=is_global
    )
    session.add(rs)
    await session.flush()
    return rs


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_rating(async_session):
    repo = RatingRepository(async_session)
    rs = await _create_rating_set(async_session)
    r = await repo.create("icon.png", uuid.uuid4(), 100, rs.id)
    assert r is not None
    assert r.icon_url == "icon.png"
    assert r.threshold == 100
    by_id = await repo.get_by_id(r.id)
    assert by_id is not None and by_id.id == r.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_rating_unreal_set(async_session):
    repo = RatingRepository(async_session)
    unreal_set_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create("icon.png", uuid.uuid4(), 100, unreal_set_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_set(async_session):
    repo = RatingRepository(async_session)
    rs1 = await _create_rating_set(async_session, name="Set1")
    rs2 = await _create_rating_set(async_session, name="Set2")
    ratings1 = [await repo.create(f"a{i}.png", uuid.uuid4(), i, rs1.id) for i in range(2)]
    ratings2 = [await repo.create(f"b{i}.png", uuid.uuid4(), i, rs2.id) for i in range(3)]
    listed1 = await repo.list_for_set(rs1.id)
    listed2 = await repo.list_for_set(rs2.id)
    assert {r.id for r in listed1} == {r.id for r in ratings1 if r is not None}
    assert {r.id for r in listed2} == {r.id for r in ratings2 if r is not None}


@pytest.mark.asyncio(loop_scope="session")
async def test_set_icon_and_threshold(async_session):
    repo = RatingRepository(async_session)
    rs = await _create_rating_set(async_session)
    r = await repo.create("icon_old.png", uuid.uuid4(), 50, rs.id)
    assert r is not None
    new_icon_id = uuid.uuid4()
    r = await repo.set_icon(r, "icon_new.png", new_icon_id)
    assert r.icon_url == "icon_new.png"
    assert r.icon_id == new_icon_id
    r = await repo.set_threshold(r, 60)
    assert r.threshold == 60


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_rating(async_session):
    repo = RatingRepository(async_session)
    rs = await _create_rating_set(async_session)
    r = await repo.create("icon_del.png", uuid.uuid4(), 10, rs.id)
    assert r is not None
    ok = await repo.delete(r.id)
    assert ok is True
    not_ok = await repo.delete(r.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_set_empty(async_session):
    repo = RatingRepository(async_session)
    rs = await _create_rating_set(async_session)
    listed = await repo.list_for_set(rs.id)
    assert listed == []
