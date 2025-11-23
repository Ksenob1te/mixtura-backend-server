import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.repo import RestrictionRepository


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_code(async_session):
    repo = RestrictionRepository(async_session)
    rc = await repo.create("BAN")
    assert rc is not None and rc.code == "BAN"
    fetched = await repo.get_by_id(rc.id)
    assert fetched is not None and fetched.id == rc.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_code_constraint(async_session):
    repo = RestrictionRepository(async_session)
    _ = await repo.create("MUTE")
    with pytest.raises(IntegrityError):
        await repo.create("MUTE")


@pytest.mark.asyncio(loop_scope="session")
async def test_list_all_codes(async_session):
    repo = RestrictionRepository(async_session)
    codes = ["KICK", "WARN", "TEMP"]
    for c in codes:
        await repo.create(c)
    listed = await repo.list_all()
    listed_codes = {x.code for x in listed}
    for c in codes:
        assert c in listed_codes


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_code(async_session):
    repo = RestrictionRepository(async_session)
    rc = await repo.create("DEL")
    assert rc is not None
    ok = await repo.delete(rc.id)
    assert ok is True
    not_ok = await repo.delete(rc.id)
    assert not_ok is False
