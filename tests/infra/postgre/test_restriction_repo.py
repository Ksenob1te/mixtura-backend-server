import uuid
import pytest

from src.infra.postgre.repo import RestrictionRepository
from src.infra.postgre import IntegrityUniqueException


@pytest.mark.asyncio(loop_scope="session")
class TestRestrictionRepository:

    async def test_create_and_get_code(self, async_session):
        repo = RestrictionRepository(async_session)
        rc = await repo.create("BAN")
        assert rc is not None and rc.code == "BAN"
        fetched = await repo.get_by_id(rc.id)
        assert fetched is not None and fetched.id == rc.id
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_unique_code_constraint(self, async_session):
        repo = RestrictionRepository(async_session)
        _ = await repo.create("MUTE")
        with pytest.raises(IntegrityUniqueException):
            await repo.create("MUTE")

    async def test_list_all_codes(self, async_session):
        repo = RestrictionRepository(async_session)
        codes = ["KICK", "WARN", "TEMP"]
        for c in codes:
            await repo.create(c)
        listed = await repo.list_all()
        listed_codes = {x.code for x in listed}
        for c in codes:
            assert c in listed_codes

    async def test_delete_code(self, async_session):
        repo = RestrictionRepository(async_session)
        rc = await repo.create("DEL")
        assert rc is not None
        ok = await repo.delete(rc.id)
        assert ok is True
        not_ok = await repo.delete(rc.id)
        assert not_ok is False

