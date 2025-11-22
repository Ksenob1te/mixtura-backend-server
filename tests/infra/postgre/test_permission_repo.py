import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.infra.postgre.models import ServerRole, ServerRolePermission, Permission, Server
from src.infra.postgre.repo import PermissionRepository


async def _create_role(session, name="Role", position: int = 0):
    server_id = uuid.uuid4()
    s = Server(id=server_id, name="Server", owner_id=uuid.uuid4(), public=False)
    r = ServerRole(server_id=server_id, name=name, position=position)
    session.add(s)
    session.add(r)
    await session.flush()
    return r


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_get_permission(async_session):
    repo = PermissionRepository(async_session)
    p = await repo.create("perm.view")
    assert p is not None
    assert p.code_name == "perm.view"
    by_id = await repo.get_by_id(p.id)
    assert by_id is not None and by_id.id == p.id
    by_code = await repo.get_by_code_name("perm.view")
    assert by_code is not None and by_code.id == p.id
    assert await repo.get_by_code_name("missing") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_unique_code_name_enforced(async_session):
    repo = PermissionRepository(async_session)
    await repo.create("perm.unique")
    with pytest.raises(IntegrityError):
        await repo.create("perm.unique")


@pytest.mark.asyncio(loop_scope="session")
async def test_list_all_permissions(async_session):
    repo = PermissionRepository(async_session)
    codes = [f"perm.list.{i}" for i in range(3)]
    for c in codes:
        await repo.create(c)
    all_perms = await repo.list_all()
    present_codes = {p.code_name for p in all_perms}
    for c in codes:
        assert c in present_codes


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_permission(async_session):
    repo = PermissionRepository(async_session)
    p = await repo.create("perm.delete")
    assert p is not None
    ok = await repo.delete(p.id)
    assert ok is True
    not_ok = await repo.delete(p.id)
    assert not_ok is False


@pytest.mark.asyncio(loop_scope="session")
async def test_assign_and_list_for_role(async_session):
    repo = PermissionRepository(async_session)
    role = await _create_role(async_session, name="R1")
    perms = [await repo.create(f"perm.role.{i}") for i in range(2)]
    for perm in perms:
        assert perm is not None
        await repo.assign_to_role(perm.id, role.id)

    assert perms[0] is not None
    await repo.assign_to_role(perms[0].id, role.id)
    listed = await repo.list_for_role(role.id)
    assert {p.id for p in listed} == {p.id for p in perms if p is not None}

    stmt = select(ServerRolePermission).where(ServerRolePermission.server_role_id == role.id)
    res = await async_session.execute(stmt)
    assert len(res.scalars().all()) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_remove_from_role(async_session):
    repo = PermissionRepository(async_session)
    role = await _create_role(async_session)
    perm = await repo.create("perm.remove")
    assert perm is not None
    await repo.assign_to_role(perm.id, role.id)
    removed = await repo.remove_from_role(perm.id, role.id)
    assert removed is True
    removed_again = await repo.remove_from_role(perm.id, role.id)
    assert removed_again is False


@pytest.mark.asyncio(loop_scope="session")
async def test_bulk_assign_to_role(async_session):
    repo = PermissionRepository(async_session)
    role = await _create_role(async_session)
    perms = [await repo.create(f"perm.bulk.{i}") for i in range(3)]
    for p in perms:
        assert p is not None
    await repo.bulk_assign_to_role(role.id, [p.id for p in perms if p is not None])
    listed = await repo.list_for_role(role.id)
    assert {p.id for p in listed} == {p.id for p in perms if p is not None}


@pytest.mark.asyncio(loop_scope="session")
async def test_list_for_role_empty_when_none_assigned(async_session):
    repo = PermissionRepository(async_session)
    role = await _create_role(async_session)
    listed = await repo.list_for_role(role.id)
    assert listed == []

