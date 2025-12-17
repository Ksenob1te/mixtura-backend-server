import uuid
import pytest

from src.infra.postgre.repo import GameRoleSetRepository
from src.infra.postgre import IntegrityUniqueException


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_role_set(async_session):
    repo = GameRoleSetRepository(async_session)
    rs = await repo.create("SetA", is_global=False)
    assert rs is not None
    assert rs.name == "SetA"
    assert rs.is_global is False
    by_id = await repo.get_by_id(rs.id)
    assert by_id is not None and by_id.id == rs.id
    by_name = await repo.get_by_name("SetA")
    assert by_name is not None and by_name.id == rs.id
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.get_by_name("MissingName") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_setters_update_fields(async_session):
    repo = GameRoleSetRepository(async_session)
    rs = await repo.create("MutSet", is_global=False)
    assert rs is not None
    rs = await repo.set_name(rs, "MutSet2")
    assert rs.name == "MutSet2"
    rs = await repo.set_global(rs, True)
    assert rs.is_global is True


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_role_set(async_session):
    repo = GameRoleSetRepository(async_session)
    rs = await repo.create("DelSet")
    assert rs is not None
    ok = await repo.delete(rs.id)
    assert ok is True
    not_ok = await repo.delete(rs.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_get_global_role_sets(async_session):
    repo = GameRoleSetRepository(async_session)
    rs1 = await repo.create("GlobalSet1", is_global=True)
    rs2 = await repo.create("GlobalSet2", is_global=True)
    rs3 = await repo.create("NonGlobalSet", is_global=False)
    globals = await repo.get_global()
    global_ids = {rs.id for rs in globals}
    assert rs1 is not None and rs2 is not None and rs3 is not None
    assert rs1.id in global_ids
    assert rs2.id in global_ids
    assert rs3.id not in global_ids


@pytest.mark.asyncio(loop_scope="session")
async def test_copy_global_role_set(async_session):
    repo = GameRoleSetRepository(async_session)
    rs = await repo.create("OriginalGlobalSet", is_global=True)
    assert rs is not None
    copied_rs = await repo.copy_global(rs)
    assert copied_rs is not None
    assert copied_rs.id != rs.id
    assert copied_rs.name == rs.name
    assert copied_rs.is_global is False
