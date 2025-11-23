import uuid
import pytest

from src.infra.postgre.models import RatingSet
from src.infra.postgre.repo import RatingSetRepository


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_rating_set(async_session):
    repo = RatingSetRepository(async_session)
    rs = await repo.create("RSetA", 0, 100, is_global=False)
    assert rs is not None
    assert rs.name == "RSetA"
    assert rs.min_rating == 0
    assert rs.max_rating == 100
    by_id = await repo.get_by_id(rs.id)
    assert by_id is not None and by_id.id == rs.id
    by_name = await repo.get_by_name("RSetA")
    assert by_name is not None and by_name.id == rs.id
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.get_by_name("MissingRatingSet") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_setters_and_bounds(async_session):
    repo = RatingSetRepository(async_session)
    rs = await repo.create("BoundSet", 10, 20)
    assert rs is not None
    rs = await repo.set_min_rating(rs, 15)
    assert rs.min_rating == 15 and rs.max_rating == 20
    rs = await repo.set_max_rating(rs, 18)
    assert rs.max_rating == 18 and rs.min_rating == 15
    rs = await repo.set_min_rating(rs, 25)
    assert rs.min_rating == rs.max_rating == 18
    rs = await repo.set_max_rating(rs, 10)
    assert rs.max_rating == rs.min_rating == 18
    rs = await repo.set_name(rs, "BoundSet2")
    assert rs.name == "BoundSet2"
    rs = await repo.set_global(rs, True)
    assert rs.is_global is True


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_rating_set(async_session):
    repo = RatingSetRepository(async_session)
    rs = await repo.create("DelRSet", 0, 5)
    assert rs is not None
    ok = await repo.delete(rs.id)
    assert ok is True
    not_ok = await repo.delete(rs.id)
    assert not_ok is False
