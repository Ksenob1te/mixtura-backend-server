import uuid
import pytest

from src.infra.postgre.models import GameRoleSet, GameRole
from src.infra.postgre.repo import GameRoleRepository
from src.infra.postgre import IntegrityUnknownException, IntegrityForeignException, IntegrityUniqueException



async def _create_role_set(session, name="Set", is_global=False):
    rs = GameRoleSet(name=name, is_global=is_global)
    session.add(rs)
    await session.flush()
    return rs


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_game_role(async_session):
    repo = GameRoleRepository(async_session)
    rs = await _create_role_set(async_session)
    role = await repo.create("Support", rs.id, 1, 3, icon_url="support.png", icon_id=uuid.uuid4(), hidden=False)
    assert role is not None
    assert role.name == "Support"
    by_id = await repo.get_by_id(role.id)
    assert by_id is not None and by_id.id == role.id
    assert await repo.get_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_game_role_invalid_role_set(async_session):
    repo = GameRoleRepository(async_session)
    invalid_role_set_id = uuid.uuid4()
    with pytest.raises(IntegrityForeignException):
        await repo.create("InvalidRole", invalid_role_set_id, 1, 2)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_set(async_session):
    repo = GameRoleRepository(async_session)
    rs1 = await _create_role_set(async_session, name="Set1")
    rs2 = await _create_role_set(async_session, name="Set2")
    r1 = await repo.create("RoleA", rs1.id, 1, 2)
    r2 = await repo.create("RoleB", rs1.id, 2, 4)
    r3 = await repo.create("RoleC", rs2.id, 1, 1)
    assert r1 is not None
    assert r2 is not None
    assert r3 is not None
    listed1 = await repo.list_for_set(rs1.id)
    listed2 = await repo.list_for_set(rs2.id)
    assert {r.id for r in listed1} == {r1.id, r2.id}
    assert {r.id for r in listed2} == {r3.id}


@pytest.mark.asyncio(loop_scope="session")
async def test_setters_update_fields(async_session):
    repo = GameRoleRepository(async_session)
    rs = await _create_role_set(async_session)
    role = await repo.create("RoleX", rs.id, 1, 2)
    assert role is not None
    role = await repo.set_name(role, "RoleY")
    assert role.name == "RoleY"
    new_icon_id = uuid.uuid4()
    role = await repo.set_icon(role, "iconY.png", new_icon_id)
    assert role.icon_url == "iconY.png" and role.icon_id == new_icon_id
    role = await repo.set_hidden(role, True)
    assert role.hidden is True
    role = await repo.set_min(role, 3)
    assert role.min_in_team == 2
    role = await repo.set_max(role, 5)
    assert role.max_in_team == 5
    role = await repo.set_min(role, 4)
    assert role.min_in_team == 4 and role.max_in_team == 5
    role = await repo.set_max(role, 3)
    assert role.max_in_team == 4


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_game_role(async_session):
    repo = GameRoleRepository(async_session)
    rs = await _create_role_set(async_session)
    role = await repo.create("DeleteMe", rs.id, 1, 1)
    assert role is not None
    ok = await repo.delete(role.id)
    assert ok is True
    not_ok = await repo.delete(role.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_set_empty(async_session):
    repo = GameRoleRepository(async_session)
    rs = await _create_role_set(async_session)
    listed = await repo.list_for_set(rs.id)
    assert listed == []
