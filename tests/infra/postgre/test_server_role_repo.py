import uuid
import pytest

from src.infra.postgre.models import Server, GameRoleSet, RatingSet, ServerRole
from src.infra.postgre.repo import ServerRoleRepository
from src.infra.postgre import IntegrityUniqueException, IntegrityForeignException


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


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_server_role(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    r = await repo.create(s.id, "RoleA", position=1)
    assert r is not None and r.name == "RoleA" and r.position == 1
    by_id = await repo.get_by_id(r.id)
    assert by_id is not None and by_id.id == r.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_server_role_unreal_server(async_session):
    repo = ServerRoleRepository(async_session)
    unreal_server_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create(unreal_server_id, "RoleX", position=0)


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_name_per_server(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    _ = await repo.create(s.id, "Dup", 0)
    with pytest.raises(IntegrityUniqueException):
        await repo.create(s.id, "Dup", 1)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_server_sorted_by_position(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    r3 = await repo.create(s.id, "R3", 3)
    r1 = await repo.create(s.id, "R1", 1)
    r2 = await repo.create(s.id, "R2", 2)
    listed = await repo.list_for_server(s.id)
    assert [r.name for r in listed] == ["R1", "R2", "R3"]


@pytest.mark.asyncio(loop_scope="session")
async def test_set_name_and_position(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    r = await repo.create(s.id, "Orig", 5)
    assert r is not None
    r = await repo.set_name(r, "NewName")
    assert r.name == "NewName"
    r2 = await repo.set_name(r, "NewName")
    assert r2.id == r.id and r2.name == "NewName"
    r = await repo.set_position(r, -10)
    assert r.position == 0
    r = await repo.set_position(r, 7)
    assert r.position == 7


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_server_role(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    r = await repo.create(s.id, "Del", 0)
    assert r is not None
    ok = await repo.delete(r.id)
    assert ok is True
    not_ok = await repo.delete(r.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_server_empty(async_session):
    repo = ServerRoleRepository(async_session)
    s = await _server(async_session)
    listed = await repo.list_for_server(s.id)
    assert listed == []
